# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Rename
        db.start_transaction()
        try:
            db.rename_column(u'dingos_factdatatype', 'name_space_id', 'namespace_id')
            db.commit_transaction()
        except:
            db.rollback_transaction()


    def backwards(self, orm):
        db.start_transaction()
        try:
            db.rename_column(u'dingos_factdatatype', 'namespace_id', 'name_space_id')
            db.commit_transaction()
        except:
            db.rollback_transaction()


    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'dingos.blobstorage': {
            'Meta': {'object_name': 'BlobStorage'},
            'content': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sha256': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'})
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
            'value_iobject_ts': ('django.db.models.fields.DateTimeField', [], {'null': 'True'})
        },
        u'dingos.factdatatype': {
            'Meta': {'unique_together': "(('name', 'namespace'),)", 'object_name': 'FactDataType'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'namespace': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dingos.DataTypeNameSpace']"})
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
            'Meta': {'unique_together': "(('value', 'fact_data_type', 'storage_location'),)", 'object_name': 'FactValue'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'fact_data_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dingos.FactDataType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'storage_location': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
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
