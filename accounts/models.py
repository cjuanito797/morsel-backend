from email.policy import default
from django.db import models
from django.contrib.auth import get_user_model
import secrets
import random
import string
from datetime import timedelta
from django.conf import settings
from django.utils import timezone

User = get_user_model()

def generate_auth_token() -> str:
    return secrets.token_urlsafe(32)

def generate_pronounceable_username(length: int = 8) -> str:
    vowels = 'aeiou'
    consonants = ''.join(set(string.ascii_lowercase) - set(vowels))
    while True:
        chars = []
        for i in range(length):
            pool = consonants if i % 2 == 0 else vowels
            chars.append(secrets.choice(pool))
        uname = ''.join(chars)
        if not User.objects.filter(username=uname).exists():
            return uname

def default_expiry() -> timezone.datetime:
    """Top level callable for expires_at default (avoids lambda)"""
    return timezone.now() + timedelta(minutes=15)

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.street}, {self.city}, {self.state}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=14)
    has_completed_onboarding = models.BooleanField(default=False)
    sms_notifications = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)

class RegistrationToken(models.Model):
    token = models.CharField(
        max_length=43,  # token_urlsafe(32) produces ~43 chars
        default=generate_auth_token,
        unique=True,
        editable=False,
        help_text="System-generated URL-safe auth token."
    )
    email = models.EmailField(
        unique=True,
        help_text="The email address of the user to be created."
    )
    username = models.CharField(
        max_length=16,
        unique=True,
        default=generate_pronounceable_username,
        editable=False,
        help_text="System-generated username, can be edited later."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this token was issued."
    )
    expires_at = models.DateTimeField(
        default=default_expiry, # use named function instead of lambda.
        help_text="When this token becomes invalid."
    )
    is_used = models.BooleanField(
        default=False,
        help_text="Set to True once the token has been exchanged for a User."
    )

    class Meta:
        ordering = ["-created_at"]

    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    def mark_used(self):
        self.is_used = True
        self.save(update_fields=["is_used"])

    def __str__(self):
        return f"{self.email} → {self.token}"