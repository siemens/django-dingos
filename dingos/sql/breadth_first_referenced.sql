-- Returns a list of all InfoObject ids and types that are referenced by any InfoObject in pklist
/*
CREATE TYPE toRender AS (
  pk     integer,
  type   text
);
*/

CREATE OR REPLACE FUNCTION breadth_first_referenced(pklist int[])
RETURNS setof toRender
AS $$
toRender = []
visited = []

def get_referenced_pk(inputlist):
	plan_query = plpy.prepare("SELECT dingos_identifier.latest_id AS pk, dingos_infoobjecttype.name AS type FROM dingos_infoobject2fact  INNER JOIN dingos_fact ON ( dingos_infoobject2fact.fact_id = dingos_fact.id ) LEFT OUTER JOIN dingos_identifier ON ( dingos_fact.value_iobject_id_id = dingos_identifier.id ) INNER JOIN dingos_nodeid ON ( dingos_infoobject2fact.node_id_id = dingos_nodeid.id ) INNER JOIN dingos_infoobject ON (dingos_identifier.latest_id = dingos_infoobject.id) INNER JOIN dingos_infoobjecttype ON (dingos_infoobjecttype.id = dingos_infoobject.iobject_type_id) WHERE (dingos_infoobject2fact.iobject_id = ANY($1) AND NOT (dingos_fact.value_iobject_id_id IS NULL)) ORDER BY dingos_nodeid.name ASC",['integer[]',])
	ret_query = plpy.execute(plan_query, [inputlist])
	ret_query = ret_query
	ret_query_set = []
	for e in ret_query:
	  global ret_query_set
	  #Eliminate duplicates
	  if [e_new['pk'] for e_new in ret_query_set].count(e['pk']) == 0:
	    ret_query_set.append(e)

	return ret_query_set

while len(pklist) > 0:
  results = get_referenced_pk(pklist)
  global visited, pklist, toRender
  newpk = [new['pk'] for new in toRender]
  for e in results:
    #Add only new InfoObjects
    if newpk.count(e['pk']) == 0:
      toRender.append(e)
  visited += pklist
  pklist = [pk for pk in newpk if pk not in visited]

return toRender
$$ LANGUAGE plpythonu
