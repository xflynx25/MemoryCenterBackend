from django.db import migrations
from .MemoryCenterBackend.settings.base import APPLICATION_NAME

def create_default_user(apps, schema_editor):
    User = apps.get_model('your_app_label', 'User')
    User.objects.create(username='admin', password='password')  # replace with your desired username and password

class Migration(migrations.Migration):

    dependencies = [
        (APPLICATION_NAME, '0001_initial'),  # replace with the last migration before this one
    ]

    operations = [
        migrations.RunPython(create_default_user),
    ]
