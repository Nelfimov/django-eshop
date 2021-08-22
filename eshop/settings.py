from pathlib import Path
import os
from decouple import config
import dj_database_url  # HEROKU

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# ALLOWED_HOSTS = ['127.0.0.1', 'django-eshop-app.herokuapp.com']
ALLOWED_HOSTS = ['127.0.0.1']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'core',
    'payment',
    'crispy_forms',
    'django_countries',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    # providers:
    # 'allauth.socialaccount.providers.amazon',
    # 'allauth.socialaccount.providers.amazon_cognito',
    # 'allauth.socialaccount.providers.apple',
    # 'allauth.socialaccount.providers.facebook',
    # 'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.github',
    # 'allauth.socialaccount.providers.instagram',
    # 'allauth.socialaccount.providers.odnoklassniki',
    'allauth.socialaccount.providers.paypal',
    'allauth.socialaccount.providers.telegram',
    # 'allauth.socialaccount.providers.tumblr',
    # 'allauth.socialaccount.providers.twitter',
    # 'allauth.socialaccount.providers.vk',
    # 'allauth.socialaccount.providers.xing',
    # 'allauth.socialaccount.providers.yandex',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # HEROKU
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'eshop.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',  # allauth
            ],
        },
    },
]

WSGI_APPLICATION = 'eshop.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.' +
        'UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.' +
        'MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.' +
        'CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.' +
        'NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# FOR HEROKU WHITENOISE
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Extra lookup directories for collectstatic to find static files
prod_db = dj_database_url.config(conn_max_age=500)
DATABASES['default'].update(prod_db)

# HEROKU END

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# allauth
AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1
LOGIN_REDIRECT_URL = '/'


# Email
# EMAIL_BACKED = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_BACKED = 'django.core.mail.backends.console.EmailBackend'

EMAIL_HOST = 'localhost'
EMAIL_PORT = '25'
EMAIL_USE_TLS = False
EMAIL_USE_SSL = False
EMAIL_FILE_PATH = '/templates/emails'
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''


# Crispy Forms
CRISPY_TEMPLATE_PACK = 'bootstrap4'


# Paypal
PAYPAL_CLIENT_ID = config('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = config('PAYPAL_CLIENT_SECRET')


# Stripe
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY')
STRIPE_PUBLIC_KEY = config('STRIPE_PUBLIC_KEY')


# Github
GITHUB_CLIENT_ID = config('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = config('GITHUB_CLIENT_SECRET')


# allauth Provide specific settings:
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_MAX_EMAIL_ADDRESSES = 1
ACCOUNT_EMAIL_MAX_LENGTH = 254
ACCOUNT_UNIQUE_EMAIL = True
SOCIALACCOUNT_EMAIL_VERIFICATION = False
SOCIALACCOUNT_EMAIL_REQUIRED = ACCOUNT_EMAIL_REQUIRED


SOCIALACCOUNT_PROVIDERS = {
    'facebook': {
        'APP': {
            'client_id': '123',
            'secret': '456',
            'key': ''
        }
    },
    # 'paypal': {
    #     # 'APP': {
    #     #     'client_id': PAYPAL_CLIENT_ID,
    #     #     'secret': PAYPAL_CLIENT_SECRET,
    #     # },
    #     'SCOPE': ['openid', 'email'],
    #     'MODE': 'test',
    #     # 'redirect_url': 'http://127.0.0.1:8000'
    # },
    'telegram': {
        'TOKEN': config('TELEGRAM_TOKEN')
    },
    # # 'github': {
    # #     # 'APP': {
    # #     #     'client_id': GITHUB_CLIENT_ID,
    # #     #     'secret': GITHUB_CLIENT_SECRET,
    # #     # },
    # #     'SCOPE': [
    # #         'read:user',
    # #         'read:email',
    #     ]
    # }
}
