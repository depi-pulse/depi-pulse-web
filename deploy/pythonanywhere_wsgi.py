# PythonAnywhere WSGI file: Web tab -> "WSGI configuration file" -> replace everything with this.
import os
import sys

project = os.path.expanduser("~/depi-pulse-web")
if project not in sys.path:
    sys.path.insert(0, project)

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
os.environ["DJANGO_DEBUG"] = "0"
with open(os.path.join(project, ".secret_key")) as f:
    os.environ["DJANGO_SECRET_KEY"] = f.read().strip()

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
