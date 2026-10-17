from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone

from apps.accounts.models import Follow

from apps.common.validators import validate_image_file

User = get_user_model()
    
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    birth_date = serializers.DateField(required=True)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    bio = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=500)
    avatar = serializers.ImageField(required=False, allow_null=True, write_only=True, validators=[validate_image_file],)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password',
            'birth_date', 'first_name', 'last_name', 'bio', 'avatar',
        ]
        read_only_fields = ['id']

    def validate_birth_date(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("A data de nascimento não pode ser no futuro.")
        return value


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()  # aceita email OU username
    password = serializers.CharField(write_only=True)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'birth_date', 'bio', 'avatar_url']
        read_only_fields = fields

class UpdateProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(
        required=False, allow_null=True, write_only=True,
        validators=[validate_image_file],
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'birth_date', 'bio', 'avatar']

    def validate_birth_date(self, value):
        if value and value > timezone.now().date():
            raise serializers.ValidationError("A data de nascimento não pode ser no futuro.")
        return value

class FollowerSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='follower.id')
    username = serializers.CharField(source='follower.username')
    first_name = serializers.CharField(source='follower.first_name')
    last_name = serializers.CharField(source='follower.last_name')
    avatar_url = serializers.CharField(source='follower.avatar_url')
    followed_at = serializers.DateTimeField(source='created_at')

    class Meta:
        model = Follow
        fields = ['id', 'username', 'first_name', 'last_name', 'avatar_url', 'followed_at']

class FollowingSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='following.id')
    username = serializers.CharField(source='following.username')
    first_name = serializers.CharField(source='following.first_name')
    last_name = serializers.CharField(source='following.last_name')
    avatar_url = serializers.CharField(source='following.avatar_url')
    followed_at = serializers.DateTimeField(source='created_at')

    class Meta:
        model = Follow
        fields = ['id', 'username', 'first_name', 'last_name', 'avatar_url', 'followed_at']