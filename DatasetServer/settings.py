"""
Django settings for DatasetServer project.

Generated by 'django-admin startproject' using Django 4.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""
import os
from pathlib import Path
import django
from django.utils.encoding import force_str
import environ

env = environ.Env(DEBUG=(bool, False))
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
PRIVATE_FILE_LOCATION = os.path.join(BASE_DIR)
PRIVATE_FILE_URL = "/"
# Take environment variables from .env file
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-ya3++8kan(4=ny+d@^g6(le^a1p@9@d2q=eqp&ksh_lrt!--$+"
REFRESH_TOKEN_SECRET = (
    "django-insecure-ya3++8kan(4=ny+d@^g6(le^a1p@9@d2q=eqp&ksh_lrt!--$+"
)
ACCESS_TOKEN_EXPIRY_MINS = 5
REFRESH_TOKEN_EXPIRY_DAYS = 7
BASE_DOMAIN = env("BASE_DOMAIN")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['http://idpbe.civicdatalab.in', 'http://43.205.200.192', 'idp.civicdatalab.in',
                 'http://localhost:3000', '*', 'idpbe.civicdatalab.in']

CORS_ORIGIN_WHITELIST = ['idpbe.civicdatalab.in', '43.205.200.192', 'idp.civicdatalab.in', 'localhost:3000']

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'referer',
    'organization',
]

CORS_ORIGIN_ALLOW_ALL = True

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "graphene_django",
    "dataset_api",
    "payment",
    "graphql_auth",
    "activity_log",
    "encrypted_json_fields",
    'storages',
]

MIDDLEWARE = [
    'DatasetServer.middleware.SimpleMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = "DatasetServer.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "DatasetServer.wsgi.application"

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": env("DB_ENGINE"),
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST"),
        "PORT": env("DB_PORT"),
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL"),
    }
}

FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

ELASTICSEARCH = env("ES_URL")

AUTH_URL = env("AUTH_URL")
PIPELINE_URL = env("PIPELINE_URL")

REDIS_HOST = env("REDIS_HOST")
REDIS_PORT = env("REDIS_PORT")

EMAIL_URL = env("EMAIL_URL")

X_FRAME_OPTIONS = "ALLOW-FROM http://localhost:3000/"

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

GRAPHENE = {"SCHEMA": "DatasetServer.schema.schema"}


# security headers 
# SECURE_BROWSER_XSS_FILTER = True  
# SECURE_HSTS_SECONDS = 31536000 
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True 
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https') 
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True




# s3 file storage - nic
AWS_ACCESS_KEY_ID = 'PGTNB49QR7JR7IYQCTXI'
AWS_SECRET_ACCESS_KEY = 'EGobXDq8aVONay7DeBA9q5pJeXhodXfXzIMf7vc0'
AWS_STORAGE_BUCKET_NAME = 'mit6c0-backup'
#AWS_S3_SIGNATURE_VERSION = 's3v4'
#AWS_S3_REGION_NAME = 'ap-south-1'
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
# AWS_S3_VERIFY = True
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage' 
AWS_S3_ENDPOINT_URL = 'https://staas-bbs1.cloud.gov.in'
# #AWS_LOCATION = 'files'
# #AWS_S3_CUSTOM_DOMAIN = 'https://dev.idp.civicdatalab.in'



# s3 file storage - aws
# AWS_ACCESS_KEY_ID = 'AKIARIP5TJ5DCZTLFFVK'
# AWS_SECRET_ACCESS_KEY = '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'
# AWS_STORAGE_BUCKET_NAME = 'idpfilebox'
# AWS_S3_SIGNATURE_VERSION = 's3v4'
# AWS_S3_REGION_NAME = 'ap-south-1'
# AWS_S3_FILE_OVERWRITE = False
# AWS_DEFAULT_ACL = None
# AWS_S3_VERIFY = True
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage' 
#AWS_LOCATION = 'files'
#AWS_S3_CUSTOM_DOMAIN = 'https://dev.idp.civicdatalab.in'



# s3 file storage - dev
# AWS_ACCESS_KEY_ID = 'AKIARIP5TJ5DCZTLFFVK'
# AWS_SECRET_ACCESS_KEY = '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'
# AWS_STORAGE_BUCKET_NAME = 'devidpfilebox'
# AWS_S3_SIGNATURE_VERSION = 's3v4'
# AWS_S3_REGION_NAME = 'ap-south-1'
# AWS_S3_FILE_OVERWRITE = False
# AWS_DEFAULT_ACL = None
# AWS_S3_VERIFY = True
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage' 
#AWS_LOCATION = 'files'
#AWS_S3_CUSTOM_DOMAIN = 'https://dev.idp.civicdatalab.in'


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = 'static/'
MEDIA_URL = 'public/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'files', 'public')
# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

FIELD_ENCRYPTION_KEY = env('FIELD_ENCRYPTION_KEY')
EJF_ENCRYPTION_KEYS = env('FIELD_ENCRYPTION_KEY')

django.utils.encoding.force_text = force_str
