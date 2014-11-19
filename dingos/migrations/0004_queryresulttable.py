# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dingos', '0003_vio2fvalue'),
    ]

    operations = [
        migrations.CreateModel(
            name='QueryResultTable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField()),
                ('token', models.SlugField(max_length=64)),
                ('key', models.CharField(max_length=128, blank=True)),
                ('value', models.CharField(max_length=2048, blank=True)),
                ('iobject', models.ForeignKey(related_name=b'query_result_set', to='dingos.InfoObject')),
                ('related_iobject', models.ForeignKey(related_name=b'+', to='dingos.InfoObject', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
