# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'FactValue'
        db.create_table(u'dingos_factvalue', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.TextField')()),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('fact_data_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dingos.FactDataType'])),
        ))
        db.send_create_signal(u'dingos', ['FactValue'])

        # Adding unique constraint on 'FactValue', fields ['value', 'fact_data_type']
        db.create_unique(u'dingos_factvalue', ['value', 'fact_data_type_id'])

        # Adding model 'FactDataType'
        db.create_table(u'dingos_factdatatype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('name_space', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dingos.DataTypeNameSpace'])),
            ('kind', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
        ))
        db.send_create_signal(u'dingos', ['FactDataType'])

        # Adding unique constraint on 'FactDataType', fields ['name', 'name_space']
        db.create_unique(u'dingos_factdatatype', ['name', 'name_space_id'])

        # Adding model 'DataTypeNameSpace'
        db.create_table(u'dingos_datatypenamespace', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uri', self.gf('django.db.models.fields.URLField')(unique=True, max_length=255)),
            ('name', self.gf('django.db.models.fields.SlugField')(max_length=50, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'dingos', ['DataTypeNameSpace'])

        # Adding model 'IdentifierNameSpace'
        db.create_table(u'dingos_identifiernamespace', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uri', self.gf('django.db.models.fields.URLField')(unique=True, max_length=255)),
            ('name', self.gf('django.db.models.fields.SlugField')(max_length=50, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'dingos', ['IdentifierNameSpace'])

        # Adding model 'FactTerm'
        db.create_table(u'dingos_factterm', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('term', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('attribute', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal(u'dingos', ['FactTerm'])

        # Adding unique constraint on 'FactTerm', fields ['term', 'attribute']
        db.create_unique(u'dingos_factterm', ['term', 'attribute'])

        # Adding model 'InfoObjectNaming'
        db.create_table(u'dingos_infoobjectnaming', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('iobject_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dingos.InfoObjectType'])),
            ('format_string', self.gf('django.db.models.fields.TextField')()),
            ('position', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
        ))
        db.send_create_signal(u'dingos', ['InfoObjectNaming'])

        # Adding model 'InfoObjectType'
        db.create_table(u'dingos_infoobjecttype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.SlugField')(max_length=30)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('iobject_family', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dingos.InfoObjectFamily'])),
            ('namespace', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dingos.DataTypeNameSpace'], blank=True)),
        ))
        db.send_create_signal(u'dingos', ['InfoObjectType'])

        # Adding unique constraint on 'InfoObjectType', fields ['name', 'iobject_family', 'namespace']
        db.create_unique(u'dingos_infoobjecttype', ['name', 'iobject_family_id', 'namespace_id'])

        # Adding model 'InfoObjectFamily'
        db.create_table(u'dingos_infoobjectfamily', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=256)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=1024, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'dingos', ['InfoObjectFamily'])

        # Adding model 'Revision'
        db.create_table(u'dingos_revision', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=32, blank=True)),
        ))
        db.send_create_signal(u'dingos', ['Revision'])

        # Adding model 'FactTerm2Type'
        db.create_table(u'dingos_factterm2type', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('fact_term', self.gf('django.db.models.fields.related.ForeignKey')(related_name='iobject_type_thru', to=orm['dingos.FactTerm'])),
            ('iobject_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='fact_term_thru', to=orm['dingos.InfoObjectType'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=1024, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'dingos', ['FactTerm2Type'])

        # Adding unique constraint on 'FactTerm2Type', fields ['iobject_type', 'fact_term']
        db.create_unique(u'dingos_factterm2type', ['iobject_type_id', 'fact_term_id'])

        # Adding M2M table for field fact_data_types on 'FactTerm2Type'
        db.create_table(u'dingos_factterm2type_fact_data_types', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('factterm2type', models.ForeignKey(orm[u'dingos.factterm2type'], null=False)),
            ('factdatatype', models.ForeignKey(orm[u'dingos.factdatatype'], null=False))
        ))
        db.create_unique(u'dingos_factterm2type_fact_data_types', ['factterm2type_id', 'factdatatype_id'])

        # Adding model 'NodeID'
        db.create_table(u'dingos_nodeid', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
        ))
        db.send_create_signal(u'dingos', ['NodeID'])

        # Adding model 'InfoObject2Fact'
        db.create_table(u'dingos_infoobject2fact', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('iobject', self.gf('django.db.models.fields.related.ForeignKey')(related_name='fact_thru', to=orm['dingos.InfoObject'])),
            ('fact', self.gf('django.db.models.fields.related.ForeignKey')(related_name='iobject_thru', to=orm['dingos.Fact'])),
            ('attributed_fact', self.gf('django.db.models.fields.related.ForeignKey')(related_name='attributes', null=True, to=orm['dingos.InfoObject2Fact'])),
            ('node_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dingos.NodeID'])),
        ))
        db.send_create_signal(u'dingos', ['InfoObject2Fact'])

        # Adding model 'Fact'
        db.create_table(u'dingos_fact', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('fact_term', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dingos.FactTerm'])),
            ('value_iobject_id', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='value_of_set', null=True, to=orm['dingos.Identifier'])),
            ('value_iobject_ts', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('value_on_disk', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'dingos', ['Fact'])

        # Adding M2M table for field fact_values on 'Fact'
        db.create_table(u'dingos_fact_fact_values', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('fact', models.ForeignKey(orm[u'dingos.fact'], null=False)),
            ('factvalue', models.ForeignKey(orm[u'dingos.factvalue'], null=False))
        ))
        db.create_unique(u'dingos_fact_fact_values', ['fact_id', 'factvalue_id'])

        # Adding model 'InfoObject'
        db.create_table(u'dingos_infoobject', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('identifier', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dingos.Identifier'])),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')()),
            ('create_timestamp', self.gf('django.db.models.fields.DateTimeField')()),
            ('iobject_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dingos.InfoObjectType'])),
            ('iobject_type_revision', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['dingos.Revision'])),
            ('iobject_family', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dingos.InfoObjectFamily'])),
            ('iobject_family_revision', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['dingos.Revision'])),
            ('uri', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(default='Unnamed', max_length=255, blank=True)),
        ))
        db.send_create_signal(u'dingos', ['InfoObject'])

        # Adding unique constraint on 'InfoObject', fields ['identifier', 'timestamp']
        db.create_unique(u'dingos_infoobject', ['identifier_id', 'timestamp'])

        # Adding model 'Identifier'
        db.create_table(u'dingos_identifier', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uid', self.gf('django.db.models.fields.SlugField')(max_length=255)),
            ('namespace', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dingos.IdentifierNameSpace'])),
            ('latest', self.gf('django.db.models.fields.related.OneToOneField')(related_name='latest_of', unique=True, null=True, to=orm['dingos.InfoObject'])),
        ))
        db.send_create_signal(u'dingos', ['Identifier'])

        # Adding unique constraint on 'Identifier', fields ['uid', 'namespace']
        db.create_unique(u'dingos_identifier', ['uid', 'namespace_id'])

        # Adding model 'Relation'
        db.create_table(u'dingos_relation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('source_id', self.gf('django.db.models.fields.related.ForeignKey')(related_name='yields_via', null=True, to=orm['dingos.Identifier'])),
            ('target_id', self.gf('django.db.models.fields.related.ForeignKey')(related_name='yielded_by_via', null=True, to=orm['dingos.Identifier'])),
            ('relation_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dingos.Fact'])),
            ('metadata_id', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', null=True, to=orm['dingos.Identifier'])),
        ))
        db.send_create_signal(u'dingos', ['Relation'])

        # Adding unique constraint on 'Relation', fields ['source_id', 'target_id', 'relation_type']
        db.create_unique(u'dingos_relation', ['source_id_id', 'target_id_id', 'relation_type_id'])

        # Adding model 'Marking2X'
        db.create_table(u'dingos_marking2x', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('marking', self.gf('django.db.models.fields.related.ForeignKey')(related_name='marked_item_thru', to=orm['dingos.InfoObject'])),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal(u'dingos', ['Marking2X'])


    def backwards(self, orm):
        # Removing unique constraint on 'Relation', fields ['source_id', 'target_id', 'relation_type']
        db.delete_unique(u'dingos_relation', ['source_id_id', 'target_id_id', 'relation_type_id'])

        # Removing unique constraint on 'Identifier', fields ['uid', 'namespace']
        db.delete_unique(u'dingos_identifier', ['uid', 'namespace_id'])

        # Removing unique constraint on 'InfoObject', fields ['identifier', 'timestamp']
        db.delete_unique(u'dingos_infoobject', ['identifier_id', 'timestamp'])

        # Removing unique constraint on 'FactTerm2Type', fields ['iobject_type', 'fact_term']
        db.delete_unique(u'dingos_factterm2type', ['iobject_type_id', 'fact_term_id'])

        # Removing unique constraint on 'InfoObjectType', fields ['name', 'iobject_family', 'namespace']
        db.delete_unique(u'dingos_infoobjecttype', ['name', 'iobject_family_id', 'namespace_id'])

        # Removing unique constraint on 'FactTerm', fields ['term', 'attribute']
        db.delete_unique(u'dingos_factterm', ['term', 'attribute'])

        # Removing unique constraint on 'FactDataType', fields ['name', 'name_space']
        db.delete_unique(u'dingos_factdatatype', ['name', 'name_space_id'])

        # Removing unique constraint on 'FactValue', fields ['value', 'fact_data_type']
        db.delete_unique(u'dingos_factvalue', ['value', 'fact_data_type_id'])

        # Deleting model 'FactValue'
        db.delete_table(u'dingos_factvalue')

        # Deleting model 'FactDataType'
        db.delete_table(u'dingos_factdatatype')

        # Deleting model 'DataTypeNameSpace'
        db.delete_table(u'dingos_datatypenamespace')

        # Deleting model 'IdentifierNameSpace'
        db.delete_table(u'dingos_identifiernamespace')

        # Deleting model 'FactTerm'
        db.delete_table(u'dingos_factterm')

        # Deleting model 'InfoObjectNaming'
        db.delete_table(u'dingos_infoobjectnaming')

        # Deleting model 'InfoObjectType'
        db.delete_table(u'dingos_infoobjecttype')

        # Deleting model 'InfoObjectFamily'
        db.delete_table(u'dingos_infoobjectfamily')

        # Deleting model 'Revision'
        db.delete_table(u'dingos_revision')

        # Deleting model 'FactTerm2Type'
        db.delete_table(u'dingos_factterm2type')

        # Removing M2M table for field fact_data_types on 'FactTerm2Type'
        db.delete_table('dingos_factterm2type_fact_data_types')

        # Deleting model 'NodeID'
        db.delete_table(u'dingos_nodeid')

        # Deleting model 'InfoObject2Fact'
        db.delete_table(u'dingos_infoobject2fact')

        # Deleting model 'Fact'
        db.delete_table(u'dingos_fact')

        # Removing M2M table for field fact_values on 'Fact'
        db.delete_table('dingos_fact_fact_values')

        # Deleting model 'InfoObject'
        db.delete_table(u'dingos_infoobject')

        # Deleting model 'Identifier'
        db.delete_table(u'dingos_identifier')

        # Deleting model 'Relation'
        db.delete_table(u'dingos_relation')

        # Deleting model 'Marking2X'
        db.delete_table(u'dingos_marking2x')


    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'dingos.datatypenamespace': {
            'Meta': {'object_name': 'DataTypeNameSpace'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'blank': 'True'}),
            'uri': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '255'})
        },
        u'dingos.fact': {
            'Meta': {'object_name': 'Fact'},
            'fact_term': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dingos.FactTerm']"}),
            'fact_values': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['dingos.FactValue']", 'null': 'True', 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value_iobject_id': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'value_of_set'", 'null': 'True', 'to': u"orm['dingos.Identifier']"}),
            'value_iobject_ts': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'value_on_disk': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'dingos.factdatatype': {
            'Meta': {'unique_together': "(('name', 'name_space'),)", 'object_name': 'FactDataType'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'name_space': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dingos.DataTypeNameSpace']"})
        },
        u'dingos.factterm': {
            'Meta': {'unique_together': "(('term', 'attribute'),)", 'object_name': 'FactTerm'},
            'attribute': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'term': ('django.db.models.fields.CharField', [], {'max_length': '512'})
        },
        u'dingos.factterm2type': {
            'Meta': {'unique_together': "(('iobject_type', 'fact_term'),)", 'object_name': 'FactTerm2Type'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'fact_data_types': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'fact_term_thru'", 'symmetrical': 'False', 'to': u"orm['dingos.FactDataType']"}),
            'fact_term': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'iobject_type_thru'", 'to': u"orm['dingos.FactTerm']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'iobject_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'fact_term_thru'", 'to': u"orm['dingos.InfoObjectType']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'})
        },
        u'dingos.factvalue': {
            'Meta': {'unique_together': "(('value', 'fact_data_type'),)", 'object_name': 'FactValue'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'fact_data_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dingos.FactDataType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        u'dingos.identifier': {
            'Meta': {'unique_together': "(('uid', 'namespace'),)", 'object_name': 'Identifier'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latest': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'latest_of'", 'unique': 'True', 'null': 'True', 'to': u"orm['dingos.InfoObject']"}),
            'namespace': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dingos.IdentifierNameSpace']"}),
            'uid': ('django.db.models.fields.SlugField', [], {'max_length': '255'})
        },
        u'dingos.identifiernamespace': {
            'Meta': {'object_name': 'IdentifierNameSpace'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'blank': 'True'}),
            'uri': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '255'})
        },
        u'dingos.infoobject': {
            'Meta': {'ordering': "['-timestamp']", 'unique_together': "(('identifier', 'timestamp'),)", 'object_name': 'InfoObject'},
            'create_timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'facts': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['dingos.Fact']", 'through': u"orm['dingos.InfoObject2Fact']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dingos.Identifier']"}),
            'iobject_family': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dingos.InfoObjectFamily']"}),
            'iobject_family_revision': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['dingos.Revision']"}),
            'iobject_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dingos.InfoObjectType']"}),
            'iobject_type_revision': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['dingos.Revision']"}),
            'name': ('django.db.models.fields.CharField', [], {'default': "'Unnamed'", 'max_length': '255', 'blank': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'uri': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        u'dingos.infoobject2fact': {
            'Meta': {'ordering': "['node_id__name']", 'object_name': 'InfoObject2Fact'},
            'attributed_fact': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'attributes'", 'null': 'True', 'to': u"orm['dingos.InfoObject2Fact']"}),
            'fact': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'iobject_thru'", 'to': u"orm['dingos.Fact']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'iobject': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'fact_thru'", 'to': u"orm['dingos.InfoObject']"}),
            'node_id': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dingos.NodeID']"})
        },
        u'dingos.infoobjectfamily': {
            'Meta': {'object_name': 'InfoObjectFamily'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '256'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'})
        },
        u'dingos.infoobjectnaming': {
            'Meta': {'ordering': "['position']", 'object_name': 'InfoObjectNaming'},
            'format_string': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'iobject_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dingos.InfoObjectType']"}),
            'position': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        },
        u'dingos.infoobjecttype': {
            'Meta': {'unique_together': "(('name', 'iobject_family', 'namespace'),)", 'object_name': 'InfoObjectType'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'iobject_family': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dingos.InfoObjectFamily']"}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '30'}),
            'namespace': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dingos.DataTypeNameSpace']", 'blank': 'True'})
        },
        u'dingos.marking2x': {
            'Meta': {'object_name': 'Marking2X'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'marking': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'marked_item_thru'", 'to': u"orm['dingos.InfoObject']"}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        u'dingos.nodeid': {
            'Meta': {'object_name': 'NodeID'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        u'dingos.relation': {
            'Meta': {'unique_together': "(('source_id', 'target_id', 'relation_type'),)", 'object_name': 'Relation'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'metadata_id': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'to': u"orm['dingos.Identifier']"}),
            'relation_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dingos.Fact']"}),
            'source_id': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'yields_via'", 'null': 'True', 'to': u"orm['dingos.Identifier']"}),
            'target_id': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'yielded_by_via'", 'null': 'True', 'to': u"orm['dingos.Identifier']"})
        },
        u'dingos.revision': {
            'Meta': {'object_name': 'Revision'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32', 'blank': 'True'})
        }
    }

    complete_apps = ['dingos']