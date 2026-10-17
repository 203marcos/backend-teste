import uuid

from django.conf import settings
from supabase import create_client

_supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

EXTENSIONS = {'image/jpeg': '.jpg', 'image/png': '.png', 'image/webp': '.webp'}


def upload_image(file, bucket):
    extension = EXTENSIONS.get(file.content_type, '.jpg')
    file_path = f"{uuid.uuid4()}{extension}"

    _supabase.storage.from_(bucket).upload(
        file_path,
        file.read(),
        {"content-type": file.content_type},
    )

    return _supabase.storage.from_(bucket).get_public_url(file_path)