# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dingos', '0002_add_vIO2FValue_view'),
    ]

    operations = [
        migrations.CreateModel(
            name='vIO2FValue',
            fields=[
            ],
            options={
                'db_table': 'vio2fvalue',
                'managed': False,
            },
            bases=(models.Model,),
        ),
    ]
