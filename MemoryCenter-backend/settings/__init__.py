print('in init')
from dotenv import load_dotenv
load_dotenv()
from .base import *

# Override with environment-specific settings
import os
import importlib
environment = os.getenv('DJANGO_ENV')
print('env is ', environment)

if environment:
    module = importlib.import_module(f'.{environment}', APPLICATION_NAME + '.settings')
    for setting in dir(module):
        if setting.isupper():
            locals()[setting] = getattr(module, setting)

