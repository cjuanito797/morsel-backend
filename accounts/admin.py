from django.contrib import admin
from .models import RegistrationToken, Profile
# Register your models here.

@admin.register(RegistrationToken)
class RegistrationTokenAdmin(admin.ModelAdmin):
    list_display = ['email', 'expires_at',]

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user',]