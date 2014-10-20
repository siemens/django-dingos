# -*- coding: utf-8 -*-
#!/usr/bin/env python
__author__ = 'mantis'

from django.db import connection
from django.conf import settings
import pickle
from dingos.dev.db_graph import Graph_DB, Edge, Node

settings.configure(
        DEBUG=True,
        USE_TZ=True,
        DATABASES={
        "default": {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'USER': 'postgres',
        'NAME': 'django',
        'PASSWORD': 'postgres123',
        'HOST': 'localhost',
        'PORT': '5432',
    }
        })


def build_graph(pklist, direction, depth):
    cursor = connection.cursor()
    cursor.callproc("build_graph", (pklist,direction,depth))
    return cursor.fetchone()


db_graph_pickled = build_graph([35],'full',1000000)[0]
db_graph = pickle.loads(db_graph_pickled)

#print(len(db_graph.nodes))

#for node,value in db_graph.nodes.items():
    #print(node)
    #print(value.attr_dic)
#for edge in db_graph.edges:
    #print(edge)
    #print(db_graph.edges[edge].attr_dic)


