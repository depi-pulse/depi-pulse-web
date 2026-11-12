#!/usr/bin/env bash
# One-time setup on a free PythonAnywhere account (run in a PythonAnywhere Bash console):
#   bash <(curl -fsSL https://raw.githubusercontent.com/depi-pulse/depi-pulse-web/main/deploy/pythonanywhere_setup.sh)
# Then: Web tab -> Add a new web app -> Manual configuration -> Python 3.11,
#       and paste deploy/pythonanywhere_wsgi.py into the WSGI file (replace USERNAME).
set -o errexit
cd "$HOME"
if [ -d depi-pulse-web ]; then git -C depi-pulse-web pull --ff-only; else git clone https://github.com/depi-pulse/depi-pulse-web.git; fi
cd depi-pulse-web
python3.11 -m venv .venv
.venv/bin/pip install --quiet -r requirements.txt
[ -f .secret_key ] || python3.11 -c 'import secrets; print(secrets.token_hex(40))' > .secret_key
export DJANGO_DEBUG=0 DJANGO_SECRET_KEY="$(cat .secret_key)"
.venv/bin/python manage.py migrate --no-input
.venv/bin/python manage.py seed_demo
.venv/bin/python manage.py collectstatic --no-input
echo "DONE: project ready in $HOME/depi-pulse-web"
