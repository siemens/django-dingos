# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import dingos.models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BlobStorage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sha256', models.CharField(unique=True, max_length=64)),
                ('content', models.TextField(blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DataTypeNameSpace',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uri', models.CharField(help_text=b"URI of namespace. Example: 'http://stix.mitre.org/default_vocabularies-1'", unique=True, max_length=255)),
                ('name', models.SlugField(help_text=b"Name of namespace. Example: 'cyboxVocabs'. This name may be used\n                                         in XML output to denote the namespace. Note, however, that\n                                         the defining characteristic of a namespace is the URI, not the\n                                         name: the name is completely exchangeable.", blank=True)),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Fact',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value_iobject_ts', models.DateTimeField(help_text=b'Used to reference a specific revision of an information\n                                                         object rather than the latest revision.', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FactDataType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b'Identifier for data type', max_length=128)),
                ('description', models.TextField(blank=True)),
                ('kind', models.SmallIntegerField(default=0, help_text=b'Governs, kind of data type.', choices=[(0, b'Unknown'), (1, b'Not vocabulary!!'), (2, b'Vocabulary value (single choice)'), (3, b'Vocabulary value (multiple choice)'), (4, b'Reference to InfoObject')])),
                ('namespace', models.ForeignKey(related_name=b'fact_data_type_set', to='dingos.DataTypeNameSpace')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FactTerm',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('term', models.CharField(help_text=b'A path-like string such as "Header/Subject"\n                                           or "Hashes/Hash/Simple_Hash_Value" ', max_length=512)),
                ('attribute', models.CharField(help_text=b'The key of an (XML) attribute that is part of the fact term (may be empty)', max_length=128)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FactTerm2Type',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(help_text=b'A human-readable title/summary of what the fact term describes for\n                                          this InfoObjectType', max_length=1024, blank=True)),
                ('description', models.TextField(help_text=b'A comprehensive description of what the fact-term is used for\n                                          in this InfoObjectType.', blank=True)),
                ('fact_data_types', models.ManyToManyField(related_name=b'fact_term_thru', to='dingos.FactDataType')),
                ('fact_term', models.ForeignKey(related_name=b'iobject_type_thru', to='dingos.FactTerm')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FactTermNamespaceMap',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('fact_term', models.ForeignKey(to='dingos.FactTerm')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FactValue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.TextField()),
                ('title', models.CharField(help_text=b'A human-readable version of the value; useful for values\n                                          that are part of standard vocabularies.', max_length=256, blank=True)),
                ('description', models.TextField(help_text=b'A helptext/description of the value; useful for values that\n                                                are part of standard vocabularies', blank=True)),
                ('storage_location', models.SmallIntegerField(default=0, help_text=b'Governs storage location of value', choices=[(0, b'in FactValues table'), (1, b'in Filesystem'), (2, b'in BLOB table')])),
                ('fact_data_type', models.ForeignKey(related_name=b'fact_value_set', to='dingos.FactDataType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Identifier',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uid', models.SlugField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='IdentifierNameSpace',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uri', models.CharField(help_text=b"URI of namespace. Example: 'http://stix.mitre.org/default_vocabularies-1'", unique=True, max_length=255)),
                ('name', models.SlugField(help_text=b"Name of namespace. Example: 'my_organization'. This name may be used\n                                         in XML output to denote the namespace. Note, however, that\n                                         the defining characteristic of a namespace is the URI, not the\n                                         name: the name is completely exchangeable.", blank=True)),
                ('image', models.ImageField(help_text=b'Image to display for this namespace.', null=True, upload_to=dingos.models.content_file_name, blank=True)),
                ('description', models.TextField(blank=True)),
                ('is_substitution', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='IdentifierNameSpaceSubstitutionMap',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('desired_namespace', models.ForeignKey(related_name=b'importer_namespaces_thru', to='dingos.IdentifierNameSpace')),
                ('importer_namespace', models.ForeignKey(related_name=b'substituted_namespaces_thru', to='dingos.IdentifierNameSpace')),
                ('substitution_namespace', models.ForeignKey(related_name=b'substitution_map', to='dingos.IdentifierNameSpace')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InfoObject',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField()),
                ('create_timestamp', models.DateTimeField()),
                ('uri', models.URLField(help_text=b'URI pointing to further\n                                       information concerning this\n                                       enrichment, e.g., the HTML\n                                       report of a malware analysis\n                                       through Cuckoo or similar.', blank=True)),
                ('name', models.CharField(default=b'Unnamed', help_text=b"Name of the information object, usually auto generated.\n                                         from type and facts flagged as 'naming'.", max_length=255, editable=False, blank=True)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InfoObject2Fact',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('attributed_fact', models.ForeignKey(related_name=b'attributes', to='dingos.InfoObject2Fact', null=True)),
                ('fact', models.ForeignKey(related_name=b'iobject_thru', to='dingos.Fact')),
                ('iobject', models.ForeignKey(related_name=b'fact_thru', to='dingos.InfoObject')),
                ('namespace_map', models.ForeignKey(to='dingos.FactTermNamespaceMap', null=True)),
            ],
            options={
                'ordering': ['node_id__name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InfoObjectFamily',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.SlugField(help_text=b'Identifier for InfoObject Family', unique=True, max_length=256)),
                ('title', models.CharField(help_text=b'A human-readable title for the InfoObject Family', max_length=1024, blank=True)),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InfoObjectNaming',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('format_string', models.TextField(help_text=b'Format string for naming the information object. The format\n                                                  string can refer to fact terms of facts that should be\n                                                  present in an Information Object of the given type.')),
                ('position', models.PositiveSmallIntegerField(verbose_name=b'Position')),
            ],
            options={
                'ordering': ['position'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InfoObjectType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.SlugField(help_text=b"Name for a type of information object, e.g., 'Email',\n                                         'File', 'Relationship', 'InvestigationStep' etc.", max_length=30)),
                ('description', models.TextField(blank=True)),
                ('iobject_family', models.ForeignKey(related_name=b'iobject_type_set', to='dingos.InfoObjectFamily', help_text=b'Associated info-object family.')),
                ('namespace', models.ForeignKey(related_name=b'iobject_type_set', blank=True, to='dingos.DataTypeNameSpace', help_text=b'Namespace of information object type.')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Marking2X',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('marking', models.ForeignKey(related_name=b'marked_item_thru', to='dingos.InfoObject')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NodeID',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PositionalNamespace',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('position', models.SmallIntegerField()),
                ('fact_term_namespace_map', models.ForeignKey(related_name=b'namespaces_thru', to='dingos.FactTermNamespaceMap')),
                ('namespace', models.ForeignKey(related_name=b'fact_term_namespace_map_thru', to='dingos.DataTypeNameSpace')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Relation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('metadata_id', models.ForeignKey(related_name=b'+', to='dingos.Identifier', help_text=b'InfoObject containing metadata about relation.', null=True)),
                ('relation_type', models.ForeignKey(help_text=b'Description of nature of relation in direction source to target.', to='dingos.Fact')),
                ('source_id', models.ForeignKey(related_name=b'yields_via', to='dingos.Identifier', help_text=b'Pointer to source iobject, i.e., the iobject from\n                                               which something was derived', null=True)),
                ('target_id', models.ForeignKey(related_name=b'yielded_by_via', to='dingos.Identifier', help_text=b'Pointer to derived iobject', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Revision',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=32, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data_kind', models.SlugField(max_length=32)),
                ('group', models.ForeignKey(to='auth.Group', null=True)),
                ('identifier', models.ForeignKey(to='dingos.Identifier', null=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='userdata',
            unique_together=set([('user', 'group', 'data_kind')]),
        ),
        migrations.AlterUniqueTogether(
            name='relation',
            unique_together=set([('source_id', 'target_id', 'relation_type')]),
        ),
        migrations.AlterUniqueTogether(
            name='infoobjecttype',
            unique_together=set([('name', 'iobject_family', 'namespace')]),
        ),
        migrations.AddField(
            model_name='infoobjectnaming',
            name='iobject_type',
            field=models.ForeignKey(related_name=b'iobject_type_set', to='dingos.InfoObjectType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='infoobject2fact',
            name='node_id',
            field=models.ForeignKey(to='dingos.NodeID'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='infoobject',
            name='facts',
            field=models.ManyToManyField(help_text=b'Facts that are content of this enrichment', to='dingos.Fact', through='dingos.InfoObject2Fact'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='infoobject',
            name='identifier',
            field=models.ForeignKey(related_name=b'iobject_set', to='dingos.Identifier'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='infoobject',
            name='iobject_family',
            field=models.ForeignKey(related_name=b'iobject_set', to='dingos.InfoObjectFamily', help_text=b"Type of enrichment, e.g. 'CYBOX'"),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='infoobject',
            name='iobject_family_revision',
            field=models.ForeignKey(related_name=b'+', to='dingos.Revision', help_text=b"Revision of enrichment type , e.g. '1.0'"),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='infoobject',
            name='iobject_type',
            field=models.ForeignKey(related_name=b'iobject_set', to='dingos.InfoObjectType', help_text=b'Each enrichment has an information object type.'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='infoobject',
            name='iobject_type_revision',
            field=models.ForeignKey(related_name=b'+', to='dingos.Revision', help_text=b'Each enrichment has an information object type.'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='infoobject',
            unique_together=set([('identifier', 'timestamp')]),
        ),
        migrations.AlterUniqueTogether(
            name='identifiernamespacesubstitutionmap',
            unique_together=set([('importer_namespace', 'desired_namespace', 'substitution_namespace')]),
        ),
        migrations.AddField(
            model_name='identifier',
            name='latest',
            field=models.OneToOneField(related_name=b'latest_of', null=True, to='dingos.InfoObject'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='identifier',
            name='namespace',
            field=models.ForeignKey(to='dingos.IdentifierNameSpace'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='identifier',
            unique_together=set([('uid', 'namespace')]),
        ),
        migrations.AlterUniqueTogether(
            name='factvalue',
            unique_together=set([('value', 'fact_data_type', 'storage_location')]),
        ),
        migrations.AddField(
            model_name='facttermnamespacemap',
            name='namespaces',
            field=models.ManyToManyField(to='dingos.DataTypeNameSpace', through='dingos.PositionalNamespace'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='factterm2type',
            name='iobject_type',
            field=models.ForeignKey(related_name=b'fact_term_thru', to='dingos.InfoObjectType'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='factterm2type',
            unique_together=set([('iobject_type', 'fact_term')]),
        ),
        migrations.AlterUniqueTogether(
            name='factterm',
            unique_together=set([('term', 'attribute')]),
        ),
        migrations.AlterUniqueTogether(
            name='factdatatype',
            unique_together=set([('name', 'namespace')]),
        ),
        migrations.AddField(
            model_name='fact',
            name='fact_term',
            field=models.ForeignKey(help_text=b'Pointer to fact term described by this fact.', to='dingos.FactTerm'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fact',
            name='fact_values',
            field=models.ManyToManyField(help_text=b'Value(s) of that fact', to='dingos.FactValue', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fact',
            name='value_iobject_id',
            field=models.ForeignKey(related_name=b'value_of_set', blank=True, to='dingos.Identifier', help_text=b'As alternative to a text-based value stored in a fact,\n                                                       an iobject can be linked. In this case, there should\n                                                       be no fact values associated with the fact.', null=True),
            preserve_default=True,
        ),
    ]
