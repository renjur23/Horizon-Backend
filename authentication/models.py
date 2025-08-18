from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """Custom user model manager where email is the unique identifier"""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_approved", True)
        extra_fields.setdefault("user_type", "admin")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ("admin", "Company Admin"),
        ("employee", "Company Employee"),
        ("guest", "Guest User"),
    )

    username = None
    email = models.EmailField(_("email address"), unique=True)
    name = models.CharField(_("Full Name"), max_length=255, blank=True)  # <-- Add this field
    user_type = models.CharField(
        max_length=20, choices=USER_TYPE_CHOICES, default="employee"
    )
    is_approved = models.BooleanField(default=False)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["user_type", "name"]

    objects = CustomUserManager()

    def __str__(self):
        return self.email