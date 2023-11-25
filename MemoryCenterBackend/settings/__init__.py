print('in init')
from dotenv import load_dotenv
load_dotenv()
from .base import *

# Override with environment-specific settings
import os
import dj_database_url
import importlib
environment = os.getenv('DJANGO_ENV')
print('env is ', environment)

# Default to SQLite for local development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Override with Postgres if DATABASE_URL is present (e.g., on Heroku)
if 'DATABASE_URL' in os.environ:
    DATABASES['default'] = dj_database_url.config(os.environ.get('DATABASE_URL'))

# Load environment-specific settings
if environment:
    module = importlib.import_module(f'.{environment}', APPLICATION_NAME + '.settings')
    for setting in dir(module):
        if setting.isupper():
            locals()[setting] = getattr(module, setting)
