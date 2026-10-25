from django.db import IntegrityError
from django.db.models import Count, Exists, OuterRef, Value
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from . import tmdb
from .models import Review, ReviewLike
from .permissions import IsAuthorOrReadOnly
from .review_serializers import ReviewSerializer
from .services import TMDB_PROVIDER, get_or_sync_movie
from .views import tmdb_error_response

DUPLICATE_REVIEW_ERROR = {"error": "Você já possui uma resenha ativa para este filme."}


def reviews_queryset(user):
    queryset = (
        Review.objects.filter(is_active=True)
        .select_related("user", "movie")
        .annotate(likes_count=Count("likes"))
    )
    if user.is_authenticated:
        liked = ReviewLike.objects.filter(review=OuterRef("pk"), user=user)
        return queryset.annotate(liked_by_me=Exists(liked))
    return queryset.annotate(liked_by_me=Value(False))


@extend_schema_view(
    get=extend_schema(
        tags=['Resenhas'],
        responses={200: ReviewSerializer(many=True)},
        description='Lista as resenhas ativas do filme, das mais recentes para as mais antigas.',
    ),
    post=extend_schema(
        tags=['Resenhas'],
        request=ReviewSerializer,
        responses={
            201: ReviewSerializer,
            400: OpenApiResponse(description='Dados inválidos ou o usuário já possui resenha ativa para o filme'),
            401: OpenApiResponse(description='Não autenticado'),
            404: OpenApiResponse(description='Filme não encontrado no TMDB'),
        },
    ),
)
class MovieReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return reviews_queryset(self.request.user).filter(
            movie__provider=TMDB_PROVIDER,
            movie__provider_movie_id=self.kwargs["tmdb_id"],
        ).order_by("-created_at")

    def create(self, request, tmdb_id):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            movie = get_or_sync_movie(tmdb_id)
        except tmdb.TMDBError as exc:
            return tmdb_error_response(exc)

        if Review.objects.filter(user=request.user, movie=movie, is_active=True).exists():
            return Response(DUPLICATE_REVIEW_ERROR, status=status.HTTP_400_BAD_REQUEST)
        try:
            review = serializer.save(user=request.user, movie=movie)
        except IntegrityError:
            return Response(DUPLICATE_REVIEW_ERROR, status=status.HTTP_400_BAD_REQUEST)

        review = reviews_queryset(request.user).get(pk=review.pk)
        return Response(self.get_serializer(review).data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(tags=['Resenhas'], responses={200: ReviewSerializer, 404: OpenApiResponse(description='Resenha não encontrada')}),
    patch=extend_schema(
        tags=['Resenhas'],
        request=ReviewSerializer,
        responses={
            200: ReviewSerializer,
            400: OpenApiResponse(description='Dados inválidos'),
            401: OpenApiResponse(description='Não autenticado'),
            403: OpenApiResponse(description='Apenas o autor pode editar a resenha'),
            404: OpenApiResponse(description='Resenha não encontrada'),
        },
    ),
    delete=extend_schema(
        tags=['Resenhas'],
        responses={
            204: OpenApiResponse(description='Resenha excluída'),
            401: OpenApiResponse(description='Não autenticado'),
            403: OpenApiResponse(description='Apenas o autor pode excluir a resenha'),
            404: OpenApiResponse(description='Resenha não encontrada'),
        },
    ),
)
class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return reviews_queryset(self.request.user)

    def perform_destroy(self, instance):
        # Exclusão lógica: libera a restrição de uma resenha ativa por filme.
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])

