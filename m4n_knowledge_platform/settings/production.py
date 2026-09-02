from .base import *  # noqa
import os

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


STATIC_ROOT = os.path.join(os.getenv('PLATFORM_APP_DIR'), 'static')
SECRET_KEY = os.getenv('PLATFORM_PROJECT_ENTROPY')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_PATH'),
        'USER': os.getenv('DB_USERNAME'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    },
}


# Email (Mailgun via Anymail)
# https://anymail.dev/en/stable/esps/mailgun/

INSTALLED_APPS = INSTALLED_APPS + ["anymail"]

EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"

ANYMAIL = {
    "MAILGUN_API_KEY": os.environ["MAILGUN_API_KEY"],
    "MAILGUN_SENDER_DOMAIN": os.environ["MAILGUN_SENDER_DOMAIN"],
}

# Mailgun's EU region uses a different API base URL than the US default.
if mailgun_api_url := os.environ.get("MAILGUN_API_URL"):
    ANYMAIL["MAILGUN_API_URL"] = mailgun_api_url

DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL", f"webmaster@{ANYMAIL['MAILGUN_SENDER_DOMAIN']}"
)
SERVER_EMAIL = DEFAULT_FROM_EMAIL
