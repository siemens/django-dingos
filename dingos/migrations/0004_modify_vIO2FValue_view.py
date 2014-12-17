# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


sql_statement = """DROP VIEW vio2fvalue;
CREATE VIEW vio2fvalue AS
SELECT
 dingos_infoobject2fact.id AS id,
 dingos_identifiernamespace.uri as iobject_identifier_uri,
 dingos_identifier.uid as iobject_identifier_uid,
 dingos_infoobject.id AS iobject_id,
 dingos_identifier.latest_id AS latest_iobject_id,
 dingos_infoobject.name AS iobject_name,
 dingos_infoobject.timestamp AS "timestamp",
 dingos_infoobject.create_timestamp AS create_timestamp,
 dingos_infoobjecttype.name AS iobject_type_name,
 dingos_infoobjectfamily.name AS iobject_family_name,
 dingos_nodeid.name as node_id,
 dingos_factterm.term AS term,
 dingos_factterm.attribute AS attribute,
 dingos_factvalue.value AS value,

 dingos_fact.value_iobject_ts as referenced_iobject_ts,
 dingos_factvalue.storage_location as value_storage_location,


 dingos_factvalue.fact_data_type_id AS fact_data_type_id,
 dingos_fact.value_iobject_id_id as referenced_iobject_identifier_id,
 dingos_identifier.id AS identifier_id,
 dingos_infoobject2fact.id AS io2f_id,
 dingos_factterm.id AS factterm_id,
 dingos_fact.id AS fact_id,
 dingos_factvalue.id AS factvalue_id
FROM
 dingos_infoobject 
 LEFT JOIN dingos_identifier ON
 (dingos_identifier.id = dingos_infoobject.identifier_id)
 LEFT JOIN dingos_infoobject2fact ON
 (dingos_infoobject2fact.iobject_id = dingos_infoobject.id)
 LEFT JOIN dingos_fact ON
 (dingos_infoobject2fact.fact_id = dingos_fact.id)
 LEFT JOIN dingos_factterm ON 
 (dingos_factterm.id = dingos_fact.fact_term_id)
 LEFT JOIN dingos_fact_fact_values ON (dingos_fact.id = dingos_fact_fact_values.fact_id)
 LEFT JOIN dingos_factvalue ON (dingos_fact_fact_values.factvalue_id = dingos_factvalue.id)
 LEFT JOIN dingos_identifiernamespace ON
 (dingos_identifier.namespace_id = dingos_identifiernamespace.id)
 LEFT JOIN dingos_infoobjectfamily ON
 (dingos_infoobject.iobject_family_id = dingos_infoobjectfamily.id)
 LEFT JOIN dingos_infoobjecttype ON
 (dingos_infoobject.iobject_type_id = dingos_infoobjecttype.id)
 LEFT JOIN dingos_nodeid ON
 (dingos_nodeid.id = dingos_infoobject2fact.node_id_id)
"""

undo_statement = """DROP VIEW vio2fvalue;
CREATE VIEW vio2fvalue AS
SELECT
 dingos_infoobject2fact.id AS id,
 dingos_identifiernamespace.uri as iobject_identifier_uri,
 dingos_identifier.uid as iobject_identifier_uid,
 dingos_infoobject.id AS iobject_id,
 dingos_identifier.latest_id AS latest_iobject_id,
 dingos_infoobject.name AS iobject_name,
 dingos_infoobject.timestamp AS "timestamp",
 dingos_infoobject.create_timestamp AS create_timestamp,
 dingos_infoobjecttype.name AS iobject_type_name,
 dingos_infoobjectfamily.name AS iobject_family_name,
 dingos_nodeid.name as node_id,
 dingos_factterm.term AS term,
 dingos_factterm.attribute AS attribute,
 dingos_factvalue.value AS value,

 dingos_fact.value_iobject_ts as referenced_iobject_ts,
 dingos_factvalue.storage_location as value_storage_location,


 dingos_factvalue.fact_data_type_id AS fact_data_type_id,
 dingos_fact.value_iobject_id_id as referenced_iobject_identifier_id,
 dingos_identifier.id AS identifier_id,
 dingos_infoobject2fact.id AS io2f_id,
 dingos_factterm.id AS factterm_id,
 dingos_fact.id AS fact_id,
 dingos_factvalue.id AS value_id
FROM
 dingos_infoobject
 LEFT JOIN dingos_identifier ON
 (dingos_identifier.id = dingos_infoobject.identifier_id)
 LEFT JOIN dingos_infoobject2fact ON
 (dingos_infoobject2fact.iobject_id = dingos_infoobject.id)
 LEFT JOIN dingos_fact ON
 (dingos_infoobject2fact.fact_id = dingos_fact.id)
 LEFT JOIN dingos_factterm ON
 (dingos_factterm.id = dingos_fact.fact_term_id)
 LEFT JOIN dingos_fact_fact_values ON (dingos_fact.id = dingos_fact_fact_values.fact_id)
 LEFT JOIN dingos_factvalue ON (dingos_fact_fact_values.factvalue_id = dingos_factvalue.id)
 LEFT JOIN dingos_identifiernamespace ON
 (dingos_identifier.namespace_id = dingos_identifiernamespace.id)
 LEFT JOIN dingos_infoobjectfamily ON
 (dingos_infoobject.iobject_family_id = dingos_infoobjectfamily.id)
 LEFT JOIN dingos_infoobjecttype ON
 (dingos_infoobject.iobject_type_id = dingos_infoobjecttype.id)
 LEFT JOIN dingos_nodeid ON
 (dingos_nodeid.id = dingos_infoobject2fact.node_id_id)"""

class Migration(migrations.Migration):

    dependencies = [
        ('dingos', '0003_vio2fvalue'),
    ]

    operations = [
        migrations.RunSQL(
            sql_statement,
            undo_statement,
        ),
    ]
