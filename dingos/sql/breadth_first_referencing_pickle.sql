-- Function build_graph(int[])
-- returns a serialized graph object

CREATE FUNCTION build_graph(pklist int[])
RETURNS text
AS $$
import pickle
from dingos.dev.db_graph import Graph_DB, Edge, Node
-- create graph to return
graph = Graph_DB()

plan_query = plpy.prepare("SELECT dingos_infoobject.id as pk, dingos_infoobjecttype.name as type FROM dingos_infoobject INNER JOIN dingos_infoobjecttype ON ( dingos_infoobject.iobject_type_id = dingos_infoobjecttype.id ) WHERE (dingos_infoobject.id = ANY($1))",['integer[]',])
ret_query = plpy.execute(plan_query, [pklist])
for e in ret_query:
  graph.add_node(e['pk'],
                {
                  'typ':e['type'],
                  'name':"NOTIMPL"
                })

visited = []
newpk =  []

def get_referencing_pk(inputlist):
	plan_query = plpy.prepare("SELECT T5.latest_id as referenced_pk, dingos_infoobject2fact.iobject_id as referencing_pk, dingos_infoobjecttype.name as type, dingos_infoobject.name as name FROM dingos_infoobject2fact INNER JOIN dingos_infoobject ON ( dingos_infoobject2fact.iobject_id = dingos_infoobject.id ) INNER JOIN dingos_identifier ON ( dingos_infoobject.id = dingos_identifier.latest_id ) INNER JOIN dingos_fact ON ( dingos_infoobject2fact.fact_id = dingos_fact.id ) LEFT OUTER JOIN dingos_identifier T5 ON ( dingos_fact.value_iobject_id_id = T5.id ) INNER JOIN dingos_nodeid ON ( dingos_infoobject2fact.node_id_id = dingos_nodeid.id ) INNER JOIN dingos_infoobjecttype ON ( dingos_infoobject.iobject_type_id = dingos_infoobjecttype.id ) WHERE (dingos_identifier.id IS NOT NULL AND T5.latest_id = ANY($1)) ORDER BY dingos_nodeid.name ASC",['integer[]',])
	ret_query = plpy.execute(plan_query, [inputlist])

	return ret_query

while len(pklist) > 0:
  results = get_referencing_pk(pklist)
  global visited, pklist
  for e in results:
    graph.add_node(e['referencing_pk'],
                  {
                  'typ':e['type'],
                  'name':e['name']
                  })
    graph.add_edge(e['referencing_pk'],e['referenced_pk'])
    if newpk.count(e['referencing_pk']) == 0:
      newpk.append(e['referencing_pk'])
  visited += pklist
  pklist = [pk for pk in newpk if pk not in visited]

ret_string = pickle.dumps(graph)
return ret_string
$$ LANGUAGE plpythonu

