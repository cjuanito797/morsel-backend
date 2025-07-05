from django.urls import path
from .views import (GoogleAuthAPIView, EmailAvailabilityCheck,
                    UsernameAvailabilityCheck, GenerateAuthToken,
                    ValidateToken, CustomUserDetailsView, UserOnboarding, UpdatePhoneNumber)

urlpatterns = [
    path('social/google/', GoogleAuthAPIView.as_view(), name='google_login'),
    path('check-email/', EmailAvailabilityCheck.as_view(), name='email_availability_check'),
    path('check-username/', UsernameAvailabilityCheck.as_view(), name='username_availability_check'),
    path('generate-auth-token/', GenerateAuthToken.as_view(), name='auth_token_generation'),
    path('validate-token/', ValidateToken.as_view(), name='token_validation'),
    path('user/', CustomUserDetailsView.as_view(), name='user_details'),
    path('update_phone_number/', UpdatePhoneNumber.as_view(), name='update_phone_number'),
    path('user-onboarding/', UserOnboarding.as_view(), name='user_onboarding'),
]