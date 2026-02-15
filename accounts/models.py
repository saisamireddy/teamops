
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ("ADMIN", "Admin"),
        ("PM", "Project Manager"),
        ("DEV", "Developer"),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="DEV")
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    bio = models.TextField(blank=True)
    invited_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invited_users",
    )
    invited_at = models.DateTimeField(null=True, blank=True)
    invite_token_hash = models.CharField(max_length=64, null=True, blank=True)
    invite_expires_at = models.DateTimeField(null=True, blank=True)
    invite_accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
