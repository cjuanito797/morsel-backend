from pathlib import Path
import os
import warnings
from dotenv import load_dotenv
import os
import openai

load_dotenv()

USE_TZ = True
TIME_ZONE = "America/Chicago"

warnings.filterwarnings("ignore", message=".*USERNAME_REQUIRED is deprecated.*")
warnings.filterwarnings("ignore", message=".*EMAIL_REQUIRED is deprecated.*")

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-_-*-05&zfh!d=(e0s%@cjot-db4&@=5*hev5-0h#wl%c&(+fdf'
DEBUG = True
ALLOWED_HOSTS = [
    "admin.juanitosmexicancb.com",
    "www.juanitosmexicancb.com",
    "juanitosmexicancb.com",
    "127.0.0.1",
    "localhost",
    "juanitos-frontend-81093019652.us-central1.run.app",
]

# Apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',

    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.apple',     # Optional for future
    'allauth.socialaccount.providers.facebook',  # Optional for future

    'dj_rest_auth',
    'dj_rest_auth.registration',

    'api.apps.ApiConfig',
    'orders.apps.OrdersConfig',
    'accounts.apps.AccountsConfig',
    'communication.apps.CommunicationConfig',
]

SITE_ID = 1

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'slip_jab_eats_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',  # required by allauth
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'slip_jab_eats_backend.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Authentication
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Allauth settings
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'  # allow both username and email login
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_LOGIN_ON_PASSWORD_RESET = True

# Email (local dev)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# dj-rest-auth config
REST_AUTH = {
    "REGISTER_SERIALIZER": "accounts.serializers.CustomRegisterSerializer",
    "USE_JWT": False,
    "SIGNUP_FIELDS": {
        "username": {"required": True},
        "email": {"required": True},
    }
}

REST_AUTH_SERIALIZERS = {
    'USER_DETAILS_SERIALIZER': 'accounts.serializers.CustomUserSerializer',
}

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.AllowAny'],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
}

REGISTRATION_TOKEN_TTL_MINUTES = 30

# Social adapter
SOCIALACCOUNT_ADAPTER = 'accounts.adapter.CustomSocialAccountAdapter'

# Static & Media
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# CORS / CSRF
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://morsel-frontend.ngrok.io",
    "https://morsel-backend.ngrok.io",
    "https://juanitos-frontend-81093019652.us-central1.run.app",
    "https://www.juanitosmexicancb.com",
]

CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://morsel-frontend.ngrok.io",
    "https://morsel-backend.ngrok.io",
    "https://juanitos-frontend-81093019652.us-central1.run.app",
    "https://www.juanitosmexicancb.com",
]

# Uber (if still in use)
UBER_CLIENT_ID = 'tIdamGN636v_Q0VD_gt_7CdMiEx2Huba'
UBER_CUSTOMER_ID = 'f000cbbe-f661-59fd-91b2-e372541b5619'
UBER_CLIENT_SECRET = 'GcRmJMaWljSDsXlE6sKwazKle5hveCnxDboi8AL3'
UBER_SCOPE = 'eats.deliveries'
UBER_TOKEN_URL = 'https://login.uber.com/oauth/v2/token'
UBER_QUOTE_URL = f'https://sandbox-api.uber.com/v1/customers/{UBER_CUSTOMER_ID}/delivery_quotes'
UBER_DISPATCH_URL = f'https://sandbox-api.uber.com/v1/customers/{UBER_CUSTOMER_ID}/deliveries'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# celery configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },

    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',  # Capture everything from DEBUG and up
    },

    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        # your app-level logs like 'api.views' will inherit from root
    },
}