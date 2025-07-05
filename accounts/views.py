import logging
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from django.contrib.auth import get_user_model
from allauth.socialaccount.models import SocialAccount
from rest_framework.throttling import AnonRateThrottle
import random
import string
from django.utils import timezone
from django.db import IntegrityError
import secrets
from datetime import timedelta
from django.http import JsonResponse
from rest_framework.permissions import AllowAny
from .models import RegistrationToken
from django.conf import settings
from dj_rest_auth.views import UserDetailsView
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from .serializers import CustomUserSerializer
from .utils import sanitize_phone_number

User = get_user_model()

class CustomUserDetailsView(UserDetailsView):
    permission_classes = [IsAuthenticated]
    serializer_class = CustomUserSerializer # <-- attatch it explicity.

    def get_object(self):
        #ensure that .profile is included
        return User.objects.select_related('profile').get(pk=self.request.user.pk)

class LimitedEmailCheckThrottle(AnonRateThrottle):
    rate = '10/min'

class UpdatePhoneNumber(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        raw_number = request.data.get('phone_number')
        formatted_number = sanitize_phone_number(raw_number)

        if not formatted_number:
            return Response({'error': 'Invalid phone number'}, status=status.HTTP_400_BAD_REQUEST)

        request.user.profile.phone_number = formatted_number
        request.user.profile.save()

        return Response({'message': 'phone number updated.'}, status=status.HTTP_200_OK)

class UserOnboarding(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        raw_number = request.data.get('phone_number')
        formatted_number = sanitize_phone_number(raw_number)

        if not formatted_number:
            return Response({'error': 'Invalid phone number'}, status=status.HTTP_400_BAD_REQUEST)

        request.user.profile.phone_number = formatted_number
        request.user.profile.has_completed_onboarding = True
        request.user.profile.save()

        return Response({'message': 'phone number updated.'}, status=status.HTTP_200_OK)


class UsernameAvailabilityCheck(APIView):
    permission_classes = []  # public

    def post(self, request):
        username = request.data.get("username", "").strip().lower()
        if not username:
            return Response({"error": "Username is required."},
                            status=status.HTTP_400_BAD_REQUEST)

        exists = User.objects.filter(username=username).exists()
        return Response({
            "available": not exists,
            "message": "Username is available." if not exists else "Username is already taken."
        }, status=status.HTTP_200_OK)


class ValidateToken(APIView):
    permission_classes = []

    def post(self, request):
        print(request.data)
        token = request.data.get('token')
        if not token:
            return Response({"valid": False, "detail": "Token is required."},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            token_obj = RegistrationToken.objects.get(token=token)

            if token_obj.expires_at < timezone.now():
                return Response({"valid": False,
                                 "detail": "Token has expired."},
                                status=status.HTTP_400_BAD_REQUEST)

            return Response({"valid": True,
                             "email": token_obj.email,
                             "username": token_obj.username})

        except RegistrationToken.DoesNotExist:
            return Response({"valid": False, "detail": "Token not found."},
                            status=status.HTTP_404_BAD_REQUEST)


class GenerateAuthToken(APIView):
    permission_classes = []  # public

    def post(self, request):
        # the email in the payload will be used in creation of new data model.
        email = request.data.get("email", "").strip().lower()
        if not email:
            return Response({"error": "Email is required."}, status=400)

        existing = RegistrationToken.objects.filter(email=email).first()
        if existing:
            if existing.expires_at < timezone.now():
                existing.delete()
            else:
                return Response({"error": "Email already in use for an active registration "
                                          "attempt.",
                                 "detail": "Please complete the previous registration or "
                                           "wait a few minutes to try again."},
                                status=status.HTTP_400_BAD_REQUEST)

        token = secrets.token_urlsafe(32)
        new_token = RegistrationToken.objects.create(email=email, token=token,
                                                     expires_at=timezone.now() + timedelta(
                                                         minutes=settings.REGISTRATION_TOKEN_TTL_MINUTES))
        print(new_token.token);
        return Response({
            "token": new_token.token,
            "username": new_token.username,
        }, status=status.HTTP_201_CREATED)


class EmailAvailabilityCheck(APIView):
    permission_classes = []  # publicly accessible

    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        if not email:
            # means that the user did not pass in an 'email'
            return Response({"error": "Email is required."},
                            status=status.HTTP_400_BAD_REQUEST)

        exists = User.objects.filter(email=email).exists()
        return Response({
            "available": not exists,
            "message": "Email is available. " if not exists else "Email is already in use."
        }, status=status.HTTP_200_OK)


class GoogleAuthAPIView(APIView):
    def post(self, request):
        token = request.data.get('credential')

        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                "987196214592-gnn0mgi6ofjsap5di3goolhlsmjqpjpe.apps.googleusercontent.com"
                # your client_id
            )

            email = idinfo['email']
            name = idinfo.get('name', '')
            user, created = User.objects.get_or_create(email=email, defaults={
                "username": email.split('@')[0], "first_name": name})

            # Optionally link to SocialAccount
            if created:
                SocialAccount.objects.create(user=user, provider="google", uid=idinfo["sub"])

            return Response({
                "email": email,
                "token": token,
                "created": created
            })

        except ValueError:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
