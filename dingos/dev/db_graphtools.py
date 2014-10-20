__author__ = "Philipp Lang"

### Graph, Node and Edge class to export graph structure from database ###

class Node():
  def __init__(self, id, attr_dic=None):
    self.id = id
    self.attr_dic = attr_dic

  def update(self, attr_dic_new):
    if self.attr_dic:
        self.attr_dic.update(attr_dic_new)
    else:
        self.attr_dic = attr_dic_new


class Edge():
  def __init__(self, start, end, attr_dic=None):
    self.start = start
    self.end = end
    self.attr_dic = attr_dic

  def update(self, attr_dic_new):
    if self.attr_dic:
        self.attr_dic.update(attr_dic_new)
    else:
        self.attr_dic = attr_dic_new


class Graph_DB():
  def __init__(self):
    self.nodes = {}
    self.edges = {}

  def add_node(self,id, node_attr_dic=None):
    if id in self.nodes:
      self.nodes[id].update(node_attr_dic)
    else:
      self.nodes[id] = Node(id, node_attr_dic)

  def add_edge(self, start, end, edge_attr_dic=None):
    if (start,end) in self.edges:
      self.edges[(start,end)].update(edge_attr_dic)

    else:
      self.edges[(start,end)] = Edge(start, end, edge_attr_dic)


def build_graph(pkslist, direction, depth, plpy):
    import pickle
    UP_STATEMENT = "SELECT dingos_infoobject2fact.iobject_id, T5.latest_id, dingos_fact.value_iobject_ts, dingos_factterm.term, dingos_factterm.attribute, dingos_nodeid.name as node_id__name, dingos_identifiernamespace.uri as iobject__identifier__namespace__uri, T9.uid as iobject__identifier__uid, dingos_infoobject.name as iobject__name, dingos_infoobjecttype.name as iobject__iobject_type__name, dingos_infoobjectfamily.name as iobject__iobject_type__iobject_family__name, T14.uri as fact__value_iobject_id__latest__identifier__namespace__uri, T13.uid as fact__value_iobject_id__latest__identifier__uid, T6.name as fact__value_iobject_id__latest__name, T15.name as latest__iobject_type__name, T16.name as latest__iobject_type__iobject_family__name FROM dingos_infoobject2fact INNER JOIN dingos_infoobject ON ( dingos_infoobject2fact.iobject_id = dingos_infoobject.id ) INNER JOIN dingos_identifier ON ( dingos_infoobject.id = dingos_identifier.latest_id ) INNER JOIN dingos_fact ON ( dingos_infoobject2fact.fact_id = dingos_fact.id ) INNER JOIN dingos_identifier T5 ON ( dingos_fact.value_iobject_id_id = T5.id ) INNER JOIN dingos_infoobject T6 ON ( T5.latest_id = T6.id ) INNER JOIN dingos_factterm ON ( dingos_fact.fact_term_id = dingos_factterm.id ) INNER JOIN dingos_nodeid ON ( dingos_infoobject2fact.node_id_id = dingos_nodeid.id ) INNER JOIN dingos_identifier T9 ON ( dingos_infoobject.identifier_id = T9.id ) INNER JOIN dingos_identifiernamespace ON ( T9.namespace_id = dingos_identifiernamespace.id ) INNER JOIN dingos_infoobjecttype ON ( dingos_infoobject.iobject_type_id = dingos_infoobjecttype.id ) INNER JOIN dingos_infoobjectfamily ON ( dingos_infoobjecttype.iobject_family_id = dingos_infoobjectfamily.id ) INNER JOIN dingos_identifier T13 ON ( T6.identifier_id = T13.id ) INNER JOIN dingos_identifiernamespace T14 ON ( T13.namespace_id = T14.id ) INNER JOIN dingos_infoobjecttype T15 ON ( T6.iobject_type_id = T15.id ) INNER JOIN dingos_infoobjectfamily T16 ON ( T15.iobject_family_id = T16.id ) WHERE (dingos_identifier.id IS NOT NULL AND T5.latest_id = ANY($1)) ORDER BY dingos_nodeid.name ASC"
    DOWN_STATEMENT = "SELECT dingos_infoobject2fact.iobject_id, dingos_identifier.latest_id, dingos_fact.value_iobject_ts, dingos_factterm.term, dingos_factterm.attribute, dingos_nodeid.name as node_id__name, dingos_identifiernamespace.uri as iobject__identifier__namespace__uri, T8.uid as iobject__identifier__uid, dingos_infoobject.name as iobject__name, dingos_infoobjecttype.name as iobject__iobject_type__name, dingos_infoobjectfamily.name as iobject__iobject_type__iobject_family__name, T13.uri as fact__value_iobject_id__latest__identifier__namespace__uri, T12.uid as fact__value_iobject_id__latest__identifier__uid, T5.name as fact__value_iobject_id__latest__name, T14.name as latest__iobject_type__name, T15.name as latest__iobject_type__iobject_family__name FROM dingos_infoobject2fact INNER JOIN dingos_infoobject ON ( dingos_infoobject2fact.iobject_id = dingos_infoobject.id ) INNER JOIN dingos_fact ON ( dingos_infoobject2fact.fact_id = dingos_fact.id ) INNER JOIN dingos_identifier ON ( dingos_fact.value_iobject_id_id = dingos_identifier.id ) LEFT OUTER JOIN dingos_infoobject T5 ON ( dingos_identifier.latest_id = T5.id ) INNER JOIN dingos_factterm ON ( dingos_fact.fact_term_id = dingos_factterm.id ) INNER JOIN dingos_nodeid ON ( dingos_infoobject2fact.node_id_id = dingos_nodeid.id ) INNER JOIN dingos_identifier T8 ON ( dingos_infoobject.identifier_id = T8.id ) INNER JOIN dingos_identifiernamespace ON ( T8.namespace_id = dingos_identifiernamespace.id ) INNER JOIN dingos_infoobjecttype ON ( dingos_infoobject.iobject_type_id = dingos_infoobjecttype.id ) INNER JOIN dingos_infoobjectfamily ON ( dingos_infoobjecttype.iobject_family_id = dingos_infoobjectfamily.id ) LEFT OUTER JOIN dingos_identifier T12 ON ( T5.identifier_id = T12.id ) LEFT OUTER JOIN dingos_identifiernamespace T13 ON ( T12.namespace_id = T13.id ) LEFT OUTER JOIN dingos_infoobjecttype T14 ON ( T5.iobject_type_id = T14.id ) LEFT OUTER JOIN dingos_infoobjectfamily T15 ON ( T14.iobject_family_id = T15.id ) WHERE (dingos_infoobject2fact.iobject_id = ANY($1) AND NOT (dingos_fact.value_iobject_id_id IS NULL)) ORDER BY dingos_nodeid.name ASC"
    ONLY_NODE_STATEMENT = "SELECT dingos_infoobject.id as iobject_id, dingos_identifiernamespace.uri as iobject__identifier__namespace__uri, dingos_identifier.uid as iobject__identifier__uid, dingos_infoobject.name as iobject__name, dingos_infoobjecttype.name as iobject__iobject_type__name, dingos_infoobjectfamily.name as iobject__iobject_type__iobject_family__name FROM dingos_infoobject INNER JOIN dingos_identifier ON ( dingos_infoobject.identifier_id = dingos_identifier.id ) INNER JOIN dingos_identifiernamespace ON (dingos_identifiernamespace.id = dingos_identifier.namespace_id) INNER JOIN dingos_infoobjecttype ON (dingos_infoobjecttype.id = dingos_infoobject.iobject_type_id) INNER JOIN dingos_infoobjectfamily ON ( dingos_infoobjecttype.iobject_family_id = dingos_infoobjectfamily.id ) WHERE (dingos_infoobject.id = ANY($1))"
    graph = Graph_DB()
    reachable_pks = set()

    def get_upwards(inputlist):
        plan_query = plpy.prepare(UP_STATEMENT, ["integer[]"])
        ret_query = plpy.execute(plan_query, (inputlist,))
        return ret_query

    def get_downwards(inputlist):
        plan_query = plpy.prepare(DOWN_STATEMENT, ["integer[]"])
        ret_query = plpy.execute(plan_query, (inputlist,))
        return ret_query

    def get_node_infos(inputlist):
        plan_query = plpy.prepare(ONLY_NODE_STATEMENT, ["integer[]"])
        ret_query = plpy.execute(plan_query, (inputlist,))
        return ret_query

    def build_graph_rec(pkslist, reachable_pks, direction, depth):
        if direction == 'full':
            turns = ['up', 'down']
        else:
            turns = [direction]

        pkToVisit = set()

        for turn in turns:

            if turn == 'up':
                results = get_upwards(list(pkslist))
            else:
                results = get_downwards(list(pkslist))

            for e in results:
                node_dic = {}
                rnode_dic = {}
                edge_dic = {}

                edge_dic['term'] = e['term']
                edge_dic['attribute'] = e['attribute']
                edge_dic['fact_node_id'] = e['node_id__name']

                node = e['iobject_id']

                if e['latest_id']:
                    rnode = e['latest_id']
                else:
                    rnode = e['value_iobject_ts']

                if node == None or rnode == None:
                    # we uncovered a link to a node that is not in the system
                    continue

                node_dic['identifier_ns'] = e['iobject__identifier__namespace__uri']
                node_dic['identifier_uid'] = e['iobject__identifier__uid']
                node_dic['name'] = e['iobject__name']
                node_dic['iobject_type'] = e['iobject__iobject_type__name']
                node_dic['iobject_type_family'] = e['iobject__iobject_type__iobject_family__name']
                graph.add_node(node, node_dic)

                rnode_dic['identifier_ns'] = e['fact__value_iobject_id__latest__identifier__namespace__uri']
                rnode_dic['identifier_uid'] = e['fact__value_iobject_id__latest__identifier__uid']
                rnode_dic['name'] = e['fact__value_iobject_id__latest__name']
                rnode_dic['iobject_type'] = e['latest__iobject_type__name']
                rnode_dic['iobject_type_family'] = e['latest__iobject_type__iobject_family__name']
                graph.add_node(rnode, rnode_dic)

                graph.add_edge(e['iobject_id'],e['latest_id'], edge_dic)

                if turn == 'up':
                    pkToVisit.add(e['iobject_id'])
                else:
                    pkToVisit.add(e['latest_id'])

            reachable_pks.add(id for id in pkslist)

        if pkToVisit.issubset(reachable_pks) or depth == 0:
            return graph
        else:
            return build_graph_rec(pkToVisit - reachable_pks,
                                   reachable_pks | pkToVisit,
                                   direction,
                                   depth-1)

    if direction == 'both':
        build_graph_rec(pkslist, reachable_pks, 'up', depth)
        reachable_pks = set()
        build_graph_rec(pkslist, reachable_pks, 'down', depth)
    else:
        build_graph_rec(pkslist, reachable_pks, direction, depth)

    nodes_without_edges = []
    for pk in pkslist:
        if not pk in graph.nodes.keys():
            nodes_without_edges.append(pk)
        if nodes_without_edges:
            node_infos = get_node_infos(nodes_without_edges)

            for node_info in node_infos:
                node_dict = {}
                node_dict['identifier_ns'] =  node_info['iobject__identifier__namespace__uri']
                node_dict['identifier_uid'] =  node_info['iobject__identifier__uid']
                node_dict['name'] = node_info['iobject__name']
                node_dict['iobject_type'] = node_info['iobject__iobject_type__name']
                node_dict['iobject_type_family'] = node_info['iobject__iobject_type__iobject_family__name']
                graph.add_node(node_info['iobject_id'],node_dict)

    graph_pickled = pickle.dumps(graph)
    return graph_pickled