from rest_framework import serializers

from apps.common.storage import upload_image
from apps.common.validators import validate_image_file
from .models import Playlist

COVER_BUCKET = "playlist-covers"


class PlaylistSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    cover = serializers.ImageField(
        required=False, allow_null=True, write_only=True,
        validators=[validate_image_file],
    )

    class Meta:
        model = Playlist
        fields = [
            'id', 'name', 'description', 'is_public', 'cover', 'cover_url',
            'owner_username', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'cover_url', 'owner_username', 'created_at', 'updated_at']

    def _apply_cover(self, validated_data):
        if 'cover' in validated_data:
            cover = validated_data.pop('cover')
            validated_data['cover_url'] = upload_image(cover, COVER_BUCKET) if cover else None

    def create(self, validated_data):
        self._apply_cover(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        self._apply_cover(validated_data)
        return super().update(instance, validated_data)