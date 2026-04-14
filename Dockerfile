FROM python:3.12-slim as dev

# Install dependencies in a virtualenv
ENV VIRTUAL_ENV=/venv

RUN useradd wagtail --create-home && mkdir /app $VIRTUAL_ENV && chown -R wagtail /app $VIRTUAL_ENV

WORKDIR /app

# Set default environment variables. They are used at build time and runtime.
# If you specify your own environment variables on Heroku or Dokku, they will
# override the ones set here. The ones below serve as sane defaults only.
#  * PATH - Make sure that Poetry is on the PATH, along with our venv
#  * PYTHONUNBUFFERED - This is useful so Python does not hold any messages
#    from being output.
#    https://docs.python.org/3.12/using/cmdline.html#envvar-PYTHONUNBUFFERED
#    https://docs.python.org/3.12/using/cmdline.html#cmdoption-u
ENV PATH=$VIRTUAL_ENV/bin:$PATH \
    PYTHONUNBUFFERED=1

# Port exposed by this container. Should default to the port used by your WSGI
# server (Gunicorn).
EXPOSE 8000

RUN apt-get update --yes --quiet && apt-get install --yes --quiet --no-install-recommends \
    build-essential

# Don't use the root user as it's an anti-pattern
USER wagtail

# Install your app's Python requirements.
RUN python -m venv $VIRTUAL_ENV
COPY requirements.txt ./
RUN pip install --no-cache -r requirements.txt

# Copy application code.
COPY --chown=wagtail . .

# Runtime command that executes when "docker run" is called, it does the
# following:
#   1. Migrate the database.
#   2. Start the application server.
# WARNING:
#   Migrating database at the same time as starting the server IS NOT THE BEST
#   PRACTICE. The database should be migrated manually or using the release
#   phase facilities of your hosting platform. This is used only so the
#   Wagtail instance can be started with a simple "docker run" command.
CMD set -xe; python manage.py createcachetable; python manage.py migrate --noinput; python manage.py runserver 0.0.0.0:8000
