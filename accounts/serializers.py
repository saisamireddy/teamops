import hashlib
import smtplib
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.mail import send_mail
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from rest_framework import serializers

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
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")

        validate_password(data["password"])
        return data

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        return User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )


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
        fields = ("email", "first_name", "last_name", "avatar", "bio")

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
    invite_pending = serializers.SerializerMethodField()

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
            "invite_pending",
        )
        read_only_fields = (
            "username",
            "date_joined",
            "last_login",
            "invited_by",
            "invited_at",
            "invite_pending",
        )

    def get_invite_pending(self, obj):
        return bool(obj.invite_token_hash and not obj.invite_accepted_at)


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
        return value.strip().lower()

    def _hash_token(self, raw_token):
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    def _build_accept_url(self, token):
        return f"{settings.INVITE_ACCEPT_BASE_URL}?token={token}"

    def _send_invite_email(self, email, first_name, inviter_name, accept_url, expires_at):
        subject = "You are invited to TeamOps"
        expiry_text = timezone.localtime(expires_at).strftime("%Y-%m-%d %H:%M %Z")
        inviter_display = inviter_name or "A TeamOps administrator"
        greeting_name = first_name or "there"
        message = (
            f"Hi {greeting_name},\n\n"
            f"{inviter_display} invited you to join TeamOps.\n"
            f"Set your password using this link:\n{accept_url}\n\n"
            f"This invitation expires on {expiry_text}.\n"
            "If you were not expecting this email, you can ignore it.\n"
        )
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

    def create(self, validated_data):
        request = self.context["request"]
        inviter = request.user
        now = timezone.now()
        expires_at = now + timedelta(hours=settings.INVITE_TOKEN_TTL_HOURS)
        raw_token = secrets.token_urlsafe(32)
        token_hash = self._hash_token(raw_token)
        email = validated_data["email"]

        inviter_name = f"{inviter.first_name} {inviter.last_name}".strip() or inviter.username

        with transaction.atomic():
            user = User.objects.filter(email__iexact=email).first()
            if user and user.invite_accepted_at:
                raise serializers.ValidationError({"email": "This user already accepted an invitation."})
            if user and not user.invite_token_hash and user.has_usable_password():
                raise serializers.ValidationError({"email": "A user with this email already exists."})

            if user is None:
                base_username = email.split("@")[0].strip().lower() or "user"
                username = base_username
                suffix = 1
                while User.objects.filter(username=username).exists():
                    suffix += 1
                    username = f"{base_username}{suffix}"
                user = User(
                    username=username,
                    email=email,
                )

            user.first_name = validated_data["first_name"].strip()
            user.last_name = validated_data["last_name"].strip()
            user.role = validated_data["role"]
            user.invited_by = inviter
            user.invited_at = now
            user.invite_expires_at = expires_at
            user.invite_token_hash = token_hash
            user.invite_accepted_at = None
            user.is_staff = user.role == "ADMIN"
            user.set_unusable_password()
            user.save()

            accept_url = self._build_accept_url(raw_token)
            try:
                self._send_invite_email(email, user.first_name, inviter_name, accept_url, expires_at)
            except (smtplib.SMTPException, OSError, DjangoValidationError) as exc:
                raise serializers.ValidationError(
                    {"email": f"Failed to send invitation email: {exc}"}
                ) from exc

        return user


class InviteAcceptSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate(self, attrs):
        token = attrs.get("token", "").strip()
        password = attrs.get("password")
        confirm_password = attrs.get("confirm_password")

        if not token:
            raise serializers.ValidationError({"token": "Invitation token is required."})
        if password != confirm_password:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        user = User.objects.filter(invite_token_hash=token_hash).first()
        if not user:
            raise serializers.ValidationError({"token": "Invitation token is invalid."})
        if user.invite_accepted_at:
            raise serializers.ValidationError({"token": "This invitation has already been used."})
        if user.invite_expires_at and user.invite_expires_at < timezone.now():
            raise serializers.ValidationError({"token": "This invitation has expired."})
        validate_password(password, user=user)

        attrs["user"] = user
        attrs["token_hash"] = token_hash
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        token_hash = self.validated_data["token_hash"]
        if not constant_time_compare(user.invite_token_hash or "", token_hash):
            raise serializers.ValidationError({"token": "Invitation token is invalid."})

        user.set_password(self.validated_data["password"])
        user.invite_accepted_at = timezone.now()
        user.invite_token_hash = None
        user.invite_expires_at = None
        user.is_active = True
        user.save(
            update_fields=[
                "password",
                "invite_accepted_at",
                "invite_token_hash",
                "invite_expires_at",
                "is_active",
            ]
        )
        return user


class InvitePreviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "role", "invite_expires_at")
