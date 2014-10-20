CREATE OR REPLACE FUNCTION test(pklist int[])
RETURNS setof toRender
AS $$
toRender = []
visited = []

plan_query = plpy.prepare("SELECT dingos_infoobject2fact.iobject_id as pk, dingos_infoobjecttype.name as type FROM dingos_infoobject2fact INNER JOIN dingos_infoobject ON ( dingos_infoobject2fact.iobject_id = dingos_infoobject.id ) INNER JOIN dingos_identifier ON ( dingos_infoobject.id = dingos_identifier.latest_id ) INNER JOIN dingos_fact ON ( dingos_infoobject2fact.fact_id = dingos_fact.id ) LEFT OUTER JOIN dingos_identifier T5 ON ( dingos_fact.value_iobject_id_id = T5.id ) INNER JOIN dingos_nodeid ON ( dingos_infoobject2fact.node_id_id = dingos_nodeid.id ) INNER JOIN dingos_infoobjecttype ON ( dingos_infoobject.iobject_type_id = dingos_infoobjecttype.id ) WHERE (dingos_identifier.id IS NOT NULL AND T5.latest_id = ANY($1)) ORDER BY dingos_nodeid.name ASC",['integer[]',])
ret_query = plpy.execute(plan_query, [pklist])
ret_query_set = []
#for dic in ret_query:
  #global ret_query_set
  #Eliminate duplicates
  #if [dic_new['pk'] for dic_new in ret_query_set].count(dic['pk']) == 0:
    #ret_query_set += dic

return ret_query

$$ LANGUAGE plpythonu