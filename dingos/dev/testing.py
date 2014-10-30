import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mantis.settings.local_psql")
from dingos.models import InfoObject, FactValue
import taggit.managers


django.setup()

object = FactValue.objects.get(id='56')
object.tags.add("testtag")
print(object)
object = InfoObject.objects.get(id='48')
object.tags.add("testtag")
print(object)
print(object.tags.similar_objects())


