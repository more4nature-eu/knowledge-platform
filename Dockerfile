FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

# Port exposed by this container. Should default to the port used by your WSGI
# server (Gunicorn).
EXPOSE 8000

RUN apt-get update --yes --quiet && apt-get install --yes --quiet --no-install-recommends \
    build-essential nodejs npm

# Install your app's Python requirements.
COPY requirements.txt ./
RUN pip install --no-cache -r requirements.txt

COPY package.json package-lock.json ./
RUN npm install

# Runtime command that executes when "docker run" is called, it does the
# following:
#   1. Migrate the database.
#   2. Start the application server.
# WARNING:
#   Migrating database at the same time as starting the server IS NOT THE BEST
#   PRACTICE. The database should be migrated manually or using the release
#   phase facilities of your hosting platform. This is used only so the
#   Wagtail instance can be started with a simple "docker run" command.
CMD ./run_dev.sh
