# Copyright (c) Siemens AG, 2014
#
# This file is part of MANTIS.  MANTIS is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#


import networkx

import networkx as nx
import pickle

from django.db.models import Count, F, Q
from django.core.urlresolvers import reverse
from dingos.models import InfoObject2Fact, InfoObject, vIO2FValue, QueryResultTable
from django.db import connection


from dingos import DINGOS_OBJECTTYPE_ICON_MAPPING

def _build_skip_query(skip_info):
    """
    Function taking a dictionary of the following form::

          {'term': 'term_to_be_skipped', 'attribute': 'attribute_to_be_skippe', 'operator': 'comparison_operator'}

    (where either 'term' or 'attribute' may be empty, but not both at the same time).

    The function generates a Django Q-object query matching facts in a InfoObject2Fact object with the
    given term and attribute (using the given comparions operator).

    """
    Q_term = None
    Q_attr = None

    if 'term' in skip_info:
        Q_term = Q(**{('fact__fact_term__term__%s' % skip_info.get('operator','exact')): skip_info['term']})
    if 'attribute' in skip_info:
        Q_attr = Q(**{'fact__fact_term__attribute__%s' % skip_info.get('operator','exact') : skip_info['attribute']})

    if Q_term and Q_attr:
        return (Q_term & Q_attr)
    elif Q_term:
        return Q_term
    elif Q_attr:
        return Q_attr
    else:
        return None


def derive_image_info(node_dict):
    image_info = DINGOS_OBJECTTYPE_ICON_MAPPING.get(node_dict['iobject_type_family'],{}).get(node_dict['iobject_type'])

def follow_references(iobject_pks,
                      direction = 'down',
                      skip_terms=None,
                      depth=100000,
                      max_nodes=0,
                      keep_graph_info=True,
                      reverse_direction=False,
                      graph = None):
    #not implemented: skip_terms
    print("############")
    print("iobject_pks:")
    print(iobject_pks)
    print("graph:")
    print(graph)

    values_list = []

    #values_list = ['iobject_id',                            #0
    #               'fact__value_iobject_id__latest__id',    #1
    #               'fact__value_iobject_ts',                #2
    #]

    if keep_graph_info:
        values_list = values_list + ['id',
                                     'identifier__namespace__uri',   #6
                                     'identifier__uid',              #7
                                     'name',                         #8
                                     'iobject_type__name',           #9
                                     'iobject_type__iobject_family__name', #10


        ]

    cursor = connection.cursor()
    try:
        cursor.callproc("build_graph_table", ([int(pk) for pk in iobject_pks],direction, depth, max_nodes))
        token = cursor.fetchone()[0]
    finally:
        cursor.close()

    if not graph:
        graph = nx.DiGraph()
        objects = InfoObject.objects.filter(query_result_set__token=token).order_by('pk').distinct('pk').values_list(*values_list)
        print objects.query

        for object in objects:
            if keep_graph_info:

                node_dict = {}


                if keep_graph_info:
                    try:
                        url = reverse('url.dingos.view.infoobject', args=[node])
                    except:
                        url = None
                    node_dict['url'] = url
                    node_dict['identifier_ns'] =  object[1]
                    node_dict['identifier_uid'] =  object[2]
                    node_dict['name'] = object[3]
                    node_dict['iobject_type'] = object[4]
                    node_dict['iobject_type_family'] = object[5]

                    graph.add_node(object[0],**node_dict)

        edges = QueryResultTable.objects.filter(token=token,related_iobject__isnull=False)



        for edge in edges:
            edge_dict = {}
            node = edge.iobject_id
            rnode = edge.related_iobject_id
            edge_dict['term'] = edge.value
            edge_dict['attribute'] = edge.value
            edge_dict['fact_node_id'] = '' # don't have that

            graph.add_edge(node,rnode,**edge_dict)


    #TODO max_nodes_reached
    graph.graph['max_nodes_reached'] = False

    for n in graph.nodes():
        if graph.node[n]:
            graph.node[n]['image'] = derive_image_info(graph.node[n])
    return graph


def follow_references_old(iobject_pks,
                      direction = 'down',
                      skip_terms=None,
                      depth=100000,
                      max_nodes=0,
                      keep_graph_info=True,
                      reverse_direction=False,
                      graph = None):
    #not implemented: skip_terms, keep_graph_info

    cursor = connection.cursor()
    try:
        cursor.callproc("build_graph", ([int(pk) for pk in iobject_pks],direction, depth, max_nodes))
        graph_serial = cursor.fetchone()
    finally:
        cursor.close()

    graph_db = pickle.loads(graph_serial[0])
    if not graph:
        graph = nx.DiGraph()
        graph.graph.update(graph_db.graph)
    for id in graph_db.nodes:
        graph.add_node(id, graph_db.nodes[id].attr_dic)
        graph.add_node(id, url = reverse('url.dingos.view.infoobject', args=[id]))
        graph.add_node(id, image = derive_image_info(graph_db.nodes[id].attr_dic))
    for id in graph_db.edges:
        graph.add_edge(graph_db.edges[id].start, graph_db.edges[id].end, graph_db.edges[id].attr_dic)
    print(graph.graph['max_nodes_reached'])
    print(len(graph))

    if reverse_direction:
        return graph.reverse()

    if keep_graph_info:
        return graph
        #return graph.node.keys()
    else:
        return graph



def follow_references__(iobject_pks,
                      direction = 'down',
                      skip_terms=None,
                      depth=100000,
                      max_nodes=0,
                      keep_graph_info=True,
                      reverse_direction=False,
                      graph = None):

    """
    Given a list of primary keys of InfoObject instances, the function calculates a reachability graph based
    on referencing of InfoObjects within a fact. The function has the following parameters:

    - direction

      Either 'down' or 'up'.

      'down' means that the graph is built by finding all InfoObjects referenced within
      a fact of one of the InfoObjects within the given list of InfoObject instances,
      and then recursing on these newly found InfoObjects.

      'up' means that the graph is built by finding all InfoObjects (only in their latest revision) that
      contain a reference to one of the InfoObjects contained in the given list of InfoObjects.

      Note that a fact can either reference an InfoObject by its identifier (meaning that always the
      latest revision is referred to) or by it primary key (meaning that a certain revision is referenced).
      Hence: the downward search may yield InfoObjects instances that do not represent the latest revision
      of an InfoObject; the upward search, conversely, can only yield InfoObject instances that represent
      the latest revision of an InfoObject.

    - skip terms:


      A list of dictionaries of the following form::

          {'term': 'term_to_be_skipped', 'attribute': 'attribute_to_be_skippe', 'operator': 'comparison_operator'}

      Each such dictionary specifies a query on term and/or attribute of a fact term. Facts with fact_terms/attributes
      that match at least one of the specified ``skip_terms`` are ignored when building the graph.

    - depth:

      Maximal recursion depth in building the graph

    - keep_graph_info

      If set to 'True', only the list of primary keys of reachable InfoObjects is returned; otherwise, full information
      about the graph (nodes and edges) is provided.


    - reverse_direction

      If set to ``True``, source and destination of an edge are reversed. This is useful if the results of an upward-traversal
      and a downward-traversal are to be combined into a single graph.
    """
    skip_terms = None

    if not graph:

        graph = networkx.MultiDiGraph()



    if not reverse_direction:
        source_label = 'source'
        dest_label = 'dest'
    else:
        source_label = 'dest'
        dest_label = 'source'


    reachable_iobject_pks = set()

    if not skip_terms:
        skip_terms = []


    # build a Q-object for each skip-term
    skip_term_queries = map(_build_skip_query,skip_terms)

    Q_skip_terms = None


    # join all Q-objects by the 'or' operator '|'
    if len(skip_term_queries) >= 1:
        # ``reduce`` is the Python version of ``foldr`` as known in functional programming::
        #
        #        reduce(+,[1,2,3,4,5],6) = (1 + (2 + (3 + (4 + (5 + 6)))))
        Q_skip_terms = reduce(lambda x, y : (x | y),skip_term_queries[1:],skip_term_queries[0])

    # We compile the list of values we want to query
    # The query will be over InfObject2Fact instances.

    values_list = ['iobject_id',                            #0
                   'fact__value_iobject_id__latest__id',    #1
                   'fact__value_iobject_ts',                #2
    ]

    if keep_graph_info:
        values_list = values_list + ['fact__fact_term__term',                 #3
                                     'fact__fact_term__attribute',            #4
                                     'node_id__name',                         #5

                                     'iobject__identifier__namespace__uri',   #6
                                     'iobject__identifier__uid',              #7
                                     'iobject__name',                         #8
                                     'iobject__iobject_type__name',           #9
                                     'iobject__iobject_type__iobject_family__name', #10

                                     'fact__value_iobject_id__latest__identifier__namespace__uri', #11
                                     'fact__value_iobject_id__latest__identifier__uid', # 12
                                     'fact__value_iobject_id__latest__name', #13
                                     'fact__value_iobject_id__latest__iobject_type__name', #14
                                     'fact__value_iobject_id__latest__iobject_type__iobject_family__name', #15


        ]

    # The real work is done in the recursive function defined below

    def follow_references_rec(iobject_pks,reachable_iobject_pks,edge_set,direction,depth,graph):

        node_count = len(graph.nodes())

        if direction in ['down','full']:
            # When going down, we need to query for IO2F instances which have one of the
            # specified list of primary keys as primary key of the InfoObject
            # to which the IO2F instance is attached
            # Furthermore, we are only interested into IO2F instances, that constitute a reference,
            # i.e., they contain a Foreignkey to an InfoObject identifier or an InfoObject revision.

            # TODO The part of the query commented out below must be added in once it is decided on how
            # to model references to specific revisions of an InfoObject
            fact_query_down = Q(iobject_id__in=iobject_pks) & ( ~Q(fact__value_iobject_id=None) )# | ~Q(fact__value_iobject_ts=None))

        if direction in ['up','full']:
            # When going up, it is the pk of the InfoObject referenced in the IO2F instance that must be contained in the
            # specified list of primary keys

            # TODO The part of the query commented out below must be added in once it is decided on how
            # to model references to specific revisions of an InfoObject

            fact_query_up = Q(iobject__latest_of__isnull=False) & Q(fact__value_iobject_id__latest__id__in=iobject_pks) #| Q(fact__value_iobject_ts__id__in=iobject_pks)

        if direction == 'full':
            turns = ['down','up']
        else:
            turns = [direction]

        next_hop_iobject_pks = set()
        for turn in turns:
            if turn == 'down':
                fact_query = fact_query_down
            else:
                fact_query = fact_query_up

            if Q_skip_terms:
                # We enrich the query with restrictions upon the fact terms to be considered
                fact_query = ~Q_skip_terms & fact_query



            reference_fact_infos = InfoObject2Fact. \
                objects.filter(fact_query).values_list(*values_list)


            edge_list = []

            for x in reference_fact_infos:
                if keep_graph_info:
                    edge_dict = {}

                    node_dict = {}

                    rnode_dict = {}


                    edge_dict['term'] = x[3],
                    edge_dict['attribute'] = x[4]
                    edge_dict['fact_node_id'] = x[5]

                node = x[0]

                if x[1]:
                    rnode = x[1]
                else:
                    rnode = x[2]

                if node == None or rnode == None:
                    # we uncovered a link to a node that is not in the system
                    continue

                if turn == 'down':
                    next_hop_iobject_pks.add(rnode)
                else:
                    next_hop_iobject_pks.add(node)

                if keep_graph_info:

                    try:
                        url = reverse('url.dingos.view.infoobject', args=[node])
                    except:
                        url = None
                    node_dict['url'] = url
                    node_dict['identifier_ns'] =  x[6]
                    node_dict['identifier_uid'] =  x[7]
                    node_dict['name'] = x[8]
                    node_dict['iobject_type'] = x[9]
                    node_dict['iobject_type_family'] = x[10]


                    graph.add_node(node,**node_dict)


                    if True: # TODO  second branch once it has been decided on how to model
                        # references to specific revisions of an InfoObject
                        try:
                            url = reverse('url.dingos.view.infoobject', args=[rnode])
                        except:
                            url = None
                        rnode_dict['url'] = url
                        rnode_dict['identifier_ns'] = x[11]
                        rnode_dict['identifier_uid'] = x[12]
                        rnode_dict['name'] = x[13]
                        rnode_dict['iobject_type'] = x[14]
                        rnode_dict['iobject_type_family'] = x[15]

                    graph.add_node(rnode,**rnode_dict)

                    if turn == 'down' or reverse_direction or direction=='full':
                        edge_dict['direction'] = 'refers_to'
                        if not (node,rnode,edge_dict['fact_node_id']) in edge_set:
                            graph.add_edge(node,rnode,**edge_dict)
                            edge_set.add((node,rnode,edge_dict['fact_node_id']))
                    else:
                        edge_dict['direction'] = 'refered_to_by'
                        if not (rnode,node,edge_dict['fact_node_id']) in edge_set:
                            edge_set.add((rnode,node,edge_dict['fact_node_id']))
                            graph.add_edge(rnode,node,**edge_dict)
                if max_nodes and (node_count + len(next_hop_iobject_pks) >= max_nodes):
                    break

        if (next_hop_iobject_pks.issubset(reachable_iobject_pks)
            or depth-1 <=0
            or (max_nodes and (node_count + len(next_hop_iobject_pks) >= max_nodes))
            ):
            if keep_graph_info:
                if (max_nodes and (node_count + len(next_hop_iobject_pks) >= max_nodes)):
                    graph.graph['max_nodes_reached'] = True
                else:
                    graph.graph['max_nodes_reached'] = False

                # add image info

                for n in graph.nodes():
                    graph.node[n]['image'] = derive_image_info(graph.node[n])

                return graph
            else:
                return reachable_iobject_pks | next_hop_iobject_pks
        else:
            return follow_references_rec(next_hop_iobject_pks - reachable_iobject_pks,
                                        reachable_iobject_pks | next_hop_iobject_pks,
                                         edge_set,
                                         direction,
                                         depth-1,
                                         graph)

    edge_set = set()


    if direction == 'both':
        reverse_direction = not reverse_direction
        follow_references_rec(iobject_pks,reachable_iobject_pks,edge_set,"up",depth,graph)
        reverse_direction = not reverse_direction
        follow_references_rec(iobject_pks,reachable_iobject_pks,edge_set,"down",depth,graph)
    else:
        follow_references_rec(iobject_pks,reachable_iobject_pks,edge_set,direction,depth,graph)

    nodes_without_edges = []
    for obj_pk in iobject_pks:
        if not obj_pk in graph.node:
            nodes_without_edges.append(obj_pk)
        if nodes_without_edges:
            node_infos = InfoObject.objects.filter(pk__in=nodes_without_edges).prefetch_related( 'identifier__namespace',
                                     'iobject_type',
                                     'iobject_type__iobject_family')

            for node_info in node_infos:
                node_dict = {}
                try:
                    url = reverse('url.dingos.view.infoobject', args=[node_info.pk])
                except:
                    url = None
                node_dict['url'] = url
                node_dict['identifier_ns'] =  node_info.identifier.namespace.uri
                node_dict['identifier_uid'] =  node_info.identifier.uid
                node_dict['name'] = node_info.name
                node_dict['iobject_type'] = node_info.iobject_type.name
                node_dict['iobject_type_family'] = node_info.iobject_type.iobject_family.name
                graph.add_node(node_info.pk,node_dict)

    return graph




