#!/usr/bin/env bash
# Build step for Render / Railway: install libraries and collect the CSS/JS files.
set -o errexit
pip install --upgrade pip
pip install -r requirements.txt
python manage.py collectstatic --no-input
