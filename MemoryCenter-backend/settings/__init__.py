from .base import *
print('in init')
# Override with environment-specific settings
import os
import importlib
environment = os.getenv('DJANGO_ENV')
if environment:
    module = importlib.import_module(f'.{DJANGO_ENV}', APPLICATION_NAME + '.settings')
    for setting in dir(module):
        if setting.isupper():
            locals()[setting] = getattr(module, setting)

