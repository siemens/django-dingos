# -*- coding: utf-8 -*-
#!/usr/bin/env python
__author__ = 'Philipp Lang'
#TESTING
from mantis.settings import local_psql
from django.conf import settings
settings.configure(local_psql)
from django.core.cache import cache
from time import sleep
import models
from dingos.models import dingos_class_map


class CachingManager(models.Manager):
    #manager to cache predefined queries
    #if a query is not cached, CachingManager calls models.Manager

    cachable_queries = {
        "InfoObjectFamily" : ['name'],
        "DataTypeNameSpace" : ['uri'],
    }

    def get_or_create(self, *args, **kwargs):
        if set(self.cachable_queries[self.model.__name__]).issubset(set(kwargs.keys())):
            return True
        else:
            return False


        #   class CachingManager(models.Manager):
        #
        # Konfiguration der Queries fuer die wir einen Cache haben wollen
        #  cachable_queries = {
        #                         # For InfoObjectFamily objects, we cache
        #                         # for answering queries by name
        #                         "InfoObjectFamily" : ['name'],
        #
        # 	                       }
        #
        # 	    def get_or_create(*args,*kwargs):
        # 	        if <kwargs entsprechen einem Query-Fall, den wir mit
        # 	            gecachten Daten loesen wollen, also
        # 	            sorted(kwargs.keys()) == cachable_queries[self.model.__name__] >:
        # 	            if <Cache existiert noch nicht>:
        # 	                <cache anlegen, am besten als Dictionary das in dingos.models als leer
        # 	                angelegt wird, z.B. dingos.cache_dict>
        # 	                all_objects = super(MantisManager, self).objects.all()
        # 	                for object in all_objects:
        # 	                   dingos.cache_dict[self.model.__name__][<tuple mit Inhalten abgefragter Feldern>] = object
        #
        # 	            if <gewuenschtes object in cache?>:
        # 	                return (0,object)
        # 	            else:
        # 	                <call zu Super von get_or_create mittels
        # 	                (created,object) =  super(CachingManager, self).get_or_create(*args,**kwargs)
        # 	                <object in cache einfuegen>
        # 	                return (created,object)
        # 	        else:
        # 	            return super(CachingManager, self).get_or_create(*args,**kwargs)

data = dingos_class_map['InfoObjectFamily'].cached_objects.get_or_create(name='test')
print(data)
































# settings.configure(
#         DEBUG=True,
#         USE_TZ=True,
#         DATABASES= {
#         "default": {
#             'ENGINE': 'django.db.backends.postgresql_psycopg2',
#             'USER': 'postgres',
#             'NAME': 'django',
#             'PASSWORD': 'postgres123',
#             'HOST': 'localhost',
#             'PORT': '5432',
#         }},
#         CACHES = {
#         "default": {
#         'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
#         'TIMEOUT' : 100000,
#         }})

# def build_graph(pklist, direction, depth):
#     cursor = connection.cursor()
#     cursor.callproc("build_graph", (pklist,direction,depth))
#     return cursor.fetchone()
#
#
# db_graph_pickled = build_graph([35],'full',1000000)[0]
# db_graph = pickle.loads(db_graph_pickled)