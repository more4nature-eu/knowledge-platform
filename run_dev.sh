#!/bin/bash
set -xe
python manage.py createcachetable
python manage.py migrate --noinput
npm run build-watch &
python manage.py runserver 0.0.0.0:8000
