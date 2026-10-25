from rest_framework import serializers

from .models import PlaylistMovie
from .serializers import MovieSummarySerializer


class PlaylistMovieSerializer(serializers.ModelSerializer):
    movie = MovieSummarySerializer(read_only=True)

    class Meta:
        model = PlaylistMovie
        fields = ["position", "added_at", "movie"]
        read_only_fields = fields


class PlaylistMovieInputSerializer(serializers.Serializer):
    tmdb_id = serializers.IntegerField(min_value=1)
