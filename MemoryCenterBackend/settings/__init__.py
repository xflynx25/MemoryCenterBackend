print('in init')
from dotenv import load_dotenv
load_dotenv()
from .base import *

# Override with environment-specific settings
import os
import dj_database_url
import importlib
DJANGO_ENV = os.environ.get('DJANGO_ENV')
print('env is ', DJANGO_ENV)

# Default to SQLite for local development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Override with Postgres if DATABASE_URL is present (e.g., on Heroku)
if 'DATABASE_URL' in os.environ:
    print('THE DATABASE WAS IN THE ENVIRON')
    DATABASES['default'] = dj_database_url.config(conn_max_age=600)
    #DATABASES['default'] = dj_database_url.config(os.environ.get('DATABASE_URL'))


# Load environment-specific settings
if DJANGO_ENV:
    module = importlib.import_module(f'.{DJANGO_ENV}', APPLICATION_NAME + '.settings')
    for setting in dir(module):
        if setting.isupper():
            locals()[setting] = getattr(module, setting)
