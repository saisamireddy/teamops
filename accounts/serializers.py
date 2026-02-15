from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.crypto import get_random_string
from django.utils import timezone

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email")

class RegisterSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("username", "email", "password", "confirm_password")
        extra_kwargs = {
            "password": {"write_only": True}
        }

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")

        validate_password(data["password"])
        return data

    def create(self, validated_data):
        validated_data.pop("confirm_password")

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )

        return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "avatar",
            "bio",
            "date_joined",
            "last_login",
            "is_active",
            "is_staff",
            "is_superuser",
        )
        read_only_fields = ("role", "date_joined", "last_login", "is_staff", "is_superuser")

class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "avatar",
            "bio",
        )

    def validate_avatar(self, file):
        if file and file.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Avatar max size 5MB")
        return file

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")

        validate_password(data["new_password"])
        return data
class AdminUserSerializer(serializers.ModelSerializer):
    """
    Serializer for Admins to Manage Users.
    Allows editing 'role' and 'is_active', unlike the standard profile serializer.
    """
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_active",
            "avatar",
            "date_joined",
            "last_login",
            "invited_by",
            "invited_at",
        )
        read_only_fields = ("username", "date_joined", "last_login", "invited_by", "invited_at")


class AdminInviteUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_active",
            "avatar",
            "date_joined",
            "last_login",
            "invited_by",
            "invited_at",
        )
        read_only_fields = (
            "id",
            "username",
            "is_active",
            "avatar",
            "date_joined",
            "last_login",
            "invited_by",
            "invited_at",
        )
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": True},
            "email": {"required": True},
            "role": {"required": True},
        }

    def validate_email(self, value):
        email = value.strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email

    def create(self, validated_data):
        request = self.context["request"]
        inviter = request.user
        email = validated_data["email"]

        base_username = email.split("@")[0].strip().lower() or "user"
        username = base_username
        suffix = 1
        while User.objects.filter(username=username).exists():
            suffix += 1
            username = f"{base_username}{suffix}"

        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=validated_data["first_name"].strip(),
            last_name=validated_data["last_name"].strip(),
            role=validated_data["role"],
            password=get_random_string(length=20),
        )

        user.invited_by = inviter
        user.invited_at = timezone.now()
        user.is_staff = user.role == "ADMIN"
        user.save(update_fields=["invited_by", "invited_at", "is_staff"])
        return user
