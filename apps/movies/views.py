from django.shortcuts import render
from django.db.models import Q
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Playlist
from .permissions import IsOwnerOrReadOnly
from .serializers import PlaylistSerializer, MovieSearchQuerySerializer
from . import tmdb
from .services import build_movie_detail, sync_movie


class PlaylistListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PlaylistSerializer

    def get_queryset(self):
        return (
            Playlist.objects
            .filter(owner=self.request.user)
            .select_related('owner')
            .order_by('-created_at')
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PlaylistDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PlaylistSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        user = self.request.user
        queryset = Playlist.objects.select_related('owner')
        if user.is_authenticated:
            return queryset.filter(Q(is_public=True) | Q(owner=user))
        return queryset.filter(is_public=True)


def tmdb_error_response(exc):
    if isinstance(exc, tmdb.TMDBNotFound):
        return Response({"error": str(exc)}, status=status.HTTP_404_NOT_FOUND)
    return Response({"error": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@extend_schema(
    tags=['Filmes'],
    parameters=[
        OpenApiParameter('q', str, description='Título a pesquisar', required=True),
        OpenApiParameter('page', int, description='Página de resultados do TMDB (1 a 500)'),
    ],
    responses={
        200: OpenApiResponse(description='Resultados da busca no TMDB'),
        400: OpenApiResponse(description='Parâmetro "q" ausente ou inválido'),
        503: OpenApiResponse(description='TMDB indisponível'),
    },
)
class MovieSearchView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        query = MovieSearchQuerySerializer(data=request.query_params)
        if not query.is_valid():
            return Response(query.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = tmdb.search_movies(query.validated_data["q"], query.validated_data["page"])
        except tmdb.TMDBError as exc:
            return tmdb_error_response(exc)

        return Response(
            {
                "page": data.get("page", 1),
                "total_pages": data.get("total_pages", 0),
                "total_results": data.get("total_results", 0),
                "results": [
                    {
                        "tmdb_id": item.get("id"),
                        "title": item.get("title"),
                        "original_title": item.get("original_title"),
                        "overview": item.get("overview"),
                        "poster_path": item.get("poster_path"),
                        "backdrop_path": item.get("backdrop_path"),
                        "release_date": item.get("release_date") or None,
                        "tmdb_rating_average": item.get("vote_average"),
                    }
                    for item in data.get("results") or []
                ],
            }
        )


@extend_schema(
    tags=['Filmes'],
    responses={
        200: OpenApiResponse(description='Detalhes do filme, contadores do Twist e estado do usuário autenticado'),
        404: OpenApiResponse(description='Filme não encontrado no TMDB'),
        503: OpenApiResponse(description='TMDB indisponível'),
    },
)
class MovieDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, tmdb_id):
        try:
            data = tmdb.get_movie(tmdb_id)
        except tmdb.TMDBError as exc:
            return tmdb_error_response(exc)

        movie = sync_movie(data)
        return Response(build_movie_detail(data, movie, request.user))
