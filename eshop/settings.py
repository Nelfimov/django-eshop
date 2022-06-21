import os
from pathlib import Path

import dj_database_url  # HEROKU
from decouple import config
from django.utils.translation import gettext_lazy as _


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', config('HOST')]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',  # Sessions
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'order',
    'core',
    'payment',
    'embed_video',
    'crispy_forms',
    'django_countries',
    'nested_admin',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    # providers:
    # 'allauth.socialaccount.providers.amazon',
    # 'allauth.socialaccount.providers.amazon_cognito',
    # 'allauth.socialaccount.providers.apple',
    # 'allauth.socialaccount.providers.facebook',
    # 'allauth.socialaccount.providers.google',
    # 'allauth.socialaccount.providers.github',
    # 'allauth.socialaccount.providers.instagram',
    # 'allauth.socialaccount.providers.odnoklassniki',
    'allauth.socialaccount.providers.paypal',
    # 'allauth.socialaccount.providers.telegram',
    # 'allauth.socialaccount.providers.tumblr',
    # 'allauth.socialaccount.providers.twitter',
    # 'allauth.socialaccount.providers.vk',
    # 'allauth.socialaccount.providers.xing',
    # 'allauth.socialaccount.providers.yandex',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # HEROKU
    'django.contrib.sessions.middleware.SessionMiddleware',  # Sessions
    'django.middleware.locale.LocaleMiddleware',  # For translation
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


LANGUAGE_CODE = 'de'

LANGUAGES = [
    ('en', _('English')),
    ('de', _('German')),
]
USE_I18N = True
USE_L10N = True
LOCALE_PATHS = [
    BASE_DIR / 'locale',
    BASE_DIR / 'cart' / 'locale',
    BASE_DIR / 'core' / 'locale',
    BASE_DIR / 'payment' / 'locale',
    BASE_DIR / 'eshop' / 'locale',
    BASE_DIR / 'order' / 'locale',
]

TIME_ZONE = 'Europe/Moscow'
USE_TZ = True


STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
# FOR HEROKU WHITENOISE
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

DATA_UPLOAD_MAX_MEMORY_SIZE = 41943040  # File upload size to 40Mb
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760

# Extra lookup directories for collectstatic to find static files
prod_db = dj_database_url.config(conn_max_age=500)
DATABASES['default'].update(prod_db)
# HEROKU END

# Default primary key field type
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
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = config('GMAIL_ACCOUNT')
EMAIL_HOST_PASSWORD = config('GMAIL_PASSWORD')
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = ('JETZT IST DIE BESTE ZEIT <'
                      + config('GMAIL_ACCOUNT') + '>')
SERVER_EMAIL = 'django@jetztistdiebestezeit.de'

ADMINS = (
    (config('ADMIN1_NAME'), config('ADMIN1_EMAIL')),
    (config('ADMIN2_NAME'), config('ADMIN2_EMAIL')),
)

# Crispy Forms
CRISPY_TEMPLATE_PACK = 'bootstrap4'

# Paypal
PAYPAL_CLIENT_ID = config('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = config('PAYPAL_CLIENT_SECRET')

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


# Sessions
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_AGE = 1209600

SOCIALACCOUNT_PROVIDERS = {
    'paypal': {
        'APP': {
            'client_id': config('PAYPAL_CLIENT_ID'),
            'secret': config('PAYPAL_CLIENT_SECRET'),
        },
        'SCOPE': ['openid', 'email'],
        'MODE': 'test',
        'redirect_url': ('http://127.0.0.1:8000/en/' +
                         'accounts/paypal/login/callback/')
    },
}
