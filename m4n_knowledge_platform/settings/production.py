from .base import *  # noqa

DEBUG = False


# Security configuration

# Ensure that the session cookie is only sent by browsers under an HTTPS connection.
# https://docs.djangoproject.com/en/stable/ref/settings/#session-cookie-secure
SESSION_COOKIE_SECURE = True

# Ensure that the CSRF cookie is only sent by browsers under an HTTPS connection.
# https://docs.djangoproject.com/en/stable/ref/settings/#csrf-cookie-secure
CSRF_COOKIE_SECURE = True

# Allow the redirect importer to work in load-balanced / cloud environments.
# https://docs.wagtail.io/en/v2.13/reference/settings.html#redirects
WAGTAIL_REDIRECTS_FILE_STORAGE = "cache"

# Force HTTPS redirect (enabled by default!)
SECURE_SSL_REDIRECT = True

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "no-referrer-when-downgrade"

# Production/Upsun settings.
if (os.getenv('PLATFORM_APPLICATION_NAME') is not None):

    # Static dir.
    if (os.getenv('PLATFORM_APP_DIR') is not None):
        STATIC_ROOT = os.path.join(os.getenv('PLATFORM_APP_DIR'), 'static')

    # Secret Key.
    if (os.getenv('PLATFORM_PROJECT_ENTROPY') is not None):
        SECRET_KEY = os.getenv('PLATFORM_PROJECT_ENTROPY')

    # Production database configuration.
    if (os.getenv('PLATFORM_ENVIRONMENT') is not None):
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': os.getenv('DATABASE_PATH'),
                'USER': os.getenv('DATABASE_USERNAME'),
                'PASSWORD': os.getenv('DATABASE_PASSWORD'),
                'HOST': os.getenv('DATABASE_HOST'),
                'PORT': os.getenv('DATABASE_PORT'),
            },
            'sqlite': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
            }
        }
