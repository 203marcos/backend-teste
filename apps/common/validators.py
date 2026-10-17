from rest_framework import serializers

MAX_IMAGE_SIZE_MB = 5
ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp']


def validate_image_file(file):
    if file.size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        raise serializers.ValidationError(f"A imagem deve ter no máximo {MAX_IMAGE_SIZE_MB}MB.")

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise serializers.ValidationError("Formato não suportado. Use JPEG, PNG ou WebP.")