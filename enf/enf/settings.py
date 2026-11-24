
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent





SECRET_KEY = os.getenv('SECRET_KEY')


DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'main',
    'cart',
    'users',
    'orders',
    'payment',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # Выбирает язык запроса: cookie django_language → язык браузера → LANGUAGE_CODE.
    # Должна стоять после SessionMiddleware и до CommonMiddleware
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'cart.middleware.CartMiddleware',
]

ROOT_URLCONF = 'enf.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                'cart.context_processors.cart_processor',
                'main.context_processors.site',
            ],
        },
    },
]

WSGI_APPLICATION = 'enf.wsgi.application'



DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB'),
        'USER': os.getenv('POSTGRES_USER'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': os.getenv('POSTGRES_HOST','db'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
        'ATOMIC_REQUESTS': True,
    }
}
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




# Язык по умолчанию — для тех, чей браузер не просит ни ru, ни en, и кто ещё не нажимал кнопку
LANGUAGE_CODE = 'ru'

LANGUAGES = [
    ('ru', 'Русский'),
    ('en', 'English'),
]

# Файлы переводов: locale/ru/LC_MESSAGES/django.po (создаются командой makemessages)
LOCALE_PATHS = [BASE_DIR / 'locale']

# Помнить выбранный язык год. По умолчанию cookie живёт только до закрытия браузера
LANGUAGE_COOKIE_AGE = 60 * 60 * 24 * 365

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True



STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



SESSION_COOKIE_AGE = 86400 #30 DNEY
SESSION_SAVE_EVERY_REQUEST = True

AUTH_USER_MODEL = 'users.CustomUser'

STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
# Имя должно совпадать с переменной в .env: иначе секрет не загрузится и webhook не сможет проверить подпись Stripe
STRIPE_WEBKOOK_SECRET_KEY = os.getenv('STRIPE_WEBKOOK_SECRET_KEY')

# Письма клиентам (подтверждение оплаты). По умолчанию они печатаются в консоль runserver.
# Для настоящей отправки задайте в .env EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend и EMAIL_HOST_*
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@localhost')