from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

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
        )
        read_only_fields = ("role", "date_joined", "last_login")

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