from rest_framework import serializers

from .models import PlaylistMovie
from .serializers import MovieSummarySerializer, PlaylistSerializer


class PlaylistMovieSerializer(serializers.ModelSerializer):
    movie = MovieSummarySerializer(read_only=True)

    class Meta:
        model = PlaylistMovie
        fields = ["position", "added_at", "movie"]
        read_only_fields = fields


class PlaylistMovieInputSerializer(serializers.Serializer):
    tmdb_id = serializers.IntegerField(min_value=1)


class PlaylistDetailSerializer(PlaylistSerializer):
    """Playlist com os filmes, na ordem de `position`.

    Espera `playlist_movies` pré-carregado (ver PlaylistDetailView.get_queryset).
    """

    movies = PlaylistMovieSerializer(source="playlist_movies", many=True, read_only=True)
    movies_count = serializers.SerializerMethodField()

    class Meta(PlaylistSerializer.Meta):
        fields = PlaylistSerializer.Meta.fields + ["movies_count", "movies"]

    def get_movies_count(self, obj) -> int:
        return len(obj.playlist_movies.all())
