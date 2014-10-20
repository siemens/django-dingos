# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dingos', '0001_initial'),
    ]

    fd = open('/home/mantis/ti/django-dingos/dingos/sql/build_graph.sql', 'r')
    sql = fd.read()
    fd = open('/home/mantis/ti/django-dingos/dingos/sql/build_graph_undo.sql', 'r')
    undo = fd.read()
    fd.close()


    operations = [
        migrations.RunSQL(
            sql,
            undo
        ),
    ]
