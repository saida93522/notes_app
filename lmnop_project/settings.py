"""
Django settings for lmnop_project project.

Generated by 'django-admin startproject' using Django 2.2.5.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'o+do-*x%zn!43h+unn!46(xp$e6&)=y63v#lj3ywjuy8cihz9f'

# SECURITY WARNING: don't run with debug turned on in production!
# for deployment
if os.getenv('GAE_INSTANCE'):
    # production
    DEBUG = False
else:
    # local development
    DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'lmn',
    'get_initial_data'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'lmnop_project.timezone.TimezoneDefault',
]

ROOT_URLCONF = 'lmnop_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'lmnop_project.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

# for deployment
if os.getenv('GAE_INSTANCE'):
    # if in production
    DATABASES = {
    # using postgres
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'lmnopdb',
            'USER': 'lmn_user',
            'PASSWORD': os.environ['LMN_DB_PW'],
            'HOST': '/cloudsql/lmn-ejjns:us-central1:lmn-db',
            'PORT': '5432',
        }
    }
elif os.getenv('LMN_PROXY'):
    # to activate, run proxy 
    # then use terminal to set (export) LMN_PROXY to something before running server
    # to go back to local db use terminal to set LMN_PROXY to nothing or start new terminal
    print('Using proxy')
    DATABASES = {
    # using postgres, connecting local app to production db
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'lmnopdb',
            'USER': 'lmn_user',
            'PASSWORD': os.environ['LMN_DB_PW'],
            'HOST': '127.0.0.1',
            'PORT': '5432',
        }
    }
else:
    print('Using local db')
    # if not in production
    DATABASES = {
        # using local db
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }



# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True




# Where to send user after successful login, and logout, if no other page is provided.
LOGIN_REDIRECT_URL = 'homepage'
LOGOUT_REDIRECT_URL = 'user_logout'


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'www/static')

# save where media files saved

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# for deployment
if os.getenv('GAE_INSTANCE'):
    # if online
    GS_STATIC_FILE_BUCKET = 'lmn-ejjns.appspot.com'
    STATIC_URL = f'https://storage.googleapis.com/{GS_STATIC_FILE_BUCKET}/static/'

    # for user uploaded images
    GS_BUCKET_NAME = 'user-concert-note-images'
    MEDIA_URL = f'https://storage.cloud.google.com/{GS_BUCKET_NAME}/media/'

    # django storages looks for this variable
    DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
    
    # it is not recognizing google.oauth2 in vscode. everything seems OK so far for deployment
    # TODO: test this when image upload feature ready/ask for advice on this one
    # in the lab this issue was resolved by deleting my env and remaking it, and reinstalling all from scratch...
    from google.oauth2 import service_account
    GS_CREDENTIALS = service_account.Credentials.from_service_account_file('lmn_credentials.json')

else:
    # if local
    STATIC_URL = '/static/'
    MEDIA_URL = '/media/'

