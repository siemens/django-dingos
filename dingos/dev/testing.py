import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mantis.settings.local_psql")
from dingos.models import InfoObject, Fact
from django.contrib.auth.models import User
from sitecats.models import Category
from django.contrib.staticfiles.views import serve


django.setup()




