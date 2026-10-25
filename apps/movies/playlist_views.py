from django.db import IntegrityError, transaction
from django.db.models import Max, Q
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import tmdb
from .models import Playlist, PlaylistMovie
from .permissions import IsOwnerOrReadOnly
from .playlist_serializers import PlaylistMovieInputSerializer, PlaylistMovieSerializer
from .services import get_local_movie, get_or_sync_movie
from .views import tmdb_error_response

DUPLICATE_MOVIE_ERROR = {"error": "Este filme já está na playlist."}


class PlaylistMovieBaseView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_playlist(self, request, pk):
        """Retorna a playlist visível (pública ou do usuário) ou None.

        Dispara 403 se a playlist for visível mas pertencer a outro usuário.
        """
        playlist = Playlist.objects.filter(Q(is_public=True) | Q(owner=request.user), pk=pk).first()
        if playlist is not None:
            self.check_object_permissions(request, playlist)
        return playlist


@extend_schema(
    tags=['Playlists'],
    request=PlaylistMovieInputSerializer,
    responses={
        201: PlaylistMovieSerializer,
        400: OpenApiResponse(description='Dados inválidos ou filme já presente na playlist'),
        401: OpenApiResponse(description='Não autenticado'),
        403: OpenApiResponse(description='Apenas o dono pode alterar a playlist'),
        404: OpenApiResponse(description='Playlist ou filme não encontrados'),
    },
)
class PlaylistMovieAddView(PlaylistMovieBaseView):
    def post(self, request, pk):
        playlist = self.get_playlist(request, pk)
        if playlist is None:
            return Response({"error": "Playlist não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        serializer = PlaylistMovieInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            movie = get_or_sync_movie(serializer.validated_data["tmdb_id"])
        except tmdb.TMDBError as exc:
            return tmdb_error_response(exc)

        if PlaylistMovie.objects.filter(playlist=playlist, movie=movie).exists():
            return Response(DUPLICATE_MOVIE_ERROR, status=status.HTTP_400_BAD_REQUEST)

        last_position = playlist.playlist_movies.aggregate(last=Max("position"))["last"]
        try:
            with transaction.atomic():
                item = PlaylistMovie.objects.create(
                    playlist=playlist,
                    movie=movie,
                    position=0 if last_position is None else last_position + 1,
                )
        except IntegrityError:
            return Response(DUPLICATE_MOVIE_ERROR, status=status.HTTP_400_BAD_REQUEST)

        playlist.save(update_fields=["updated_at"])
        return Response(PlaylistMovieSerializer(item).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['Playlists'],
    responses={
        204: OpenApiResponse(description='Filme removido da playlist'),
        401: OpenApiResponse(description='Não autenticado'),
        403: OpenApiResponse(description='Apenas o dono pode alterar a playlist'),
        404: OpenApiResponse(description='Playlist ou filme não encontrados'),
    },
)
class PlaylistMovieRemoveView(PlaylistMovieBaseView):
    def delete(self, request, pk, tmdb_id):
        playlist = self.get_playlist(request, pk)
        movie = get_local_movie(tmdb_id)
        if playlist is None or movie is None:
            return Response({"error": "Playlist ou filme não encontrados."}, status=status.HTTP_404_NOT_FOUND)

        deleted, _ = PlaylistMovie.objects.filter(playlist=playlist, movie=movie).delete()
        if not deleted:
            return Response({"error": "Filme não está na playlist."}, status=status.HTTP_404_NOT_FOUND)

        playlist.save(update_fields=["updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)
