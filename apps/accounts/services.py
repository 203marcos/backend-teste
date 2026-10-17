from django.contrib.auth import get_user_model

from apps.common.storage import upload_image

User = get_user_model()

AVATAR_BUCKET = "avatars"

def register_user(
    username, email, password, birth_date=None,
    first_name='', last_name='', bio=None, avatar=None,
):
    avatar_url = upload_image(avatar, AVATAR_BUCKET) if avatar else None

    return User.objects.create_user(
        username=username,
        email=email,
        password=password,
        birth_date=birth_date,
        first_name=first_name,
        last_name=last_name,
        bio=bio,
        avatar_url=avatar_url,
    )


def login_user(identifier, password):
    try:
        user = User.objects.get(email=identifier)
    except User.DoesNotExist:
        try:
            user = User.objects.get(username=identifier)
        except User.DoesNotExist:
            return None

    if user.check_password(password):
        return user
    return None


def update_profile(user, validated_data):
    avatar = validated_data.pop('avatar', None)
    if avatar:
        validated_data['avatar_url'] = upload_image(avatar, AVATAR_BUCKET)

    for field, value in validated_data.items():
        setattr(user, field, value)

    user.save()
    return user