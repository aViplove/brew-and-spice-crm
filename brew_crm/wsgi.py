"""WSGI config for brew_crm project."""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'brew_crm.settings')
application = get_wsgi_application()
