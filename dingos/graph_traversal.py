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

from django.db.models import Count, F, Q
from django.core.urlresolvers import reverse
from dingos.models import InfoObject2Fact, InfoObject


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


def follow_references(iobject_pks,
                      direction = 'down',
                      skip_terms=None,
                      depth=100000,
                      keep_graph_info=True,
                      reverse_direction=False):
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
    else:
        Q_skip_terms = skip_term_queries[0]


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

                                     'fact__value_iobject_id__latest__identifier__namespace__uri', #10
                                     'fact__value_iobject_id__latest__identifier__uid', # 11
                                     'fact__value_iobject_id__latest__name', #12
                                     'fact__value_iobject_id__latest__iobject_type__name', #13


        ]

    # The real work is done in the recursive function defined below

    def follow_references_rec(iobject_pks,reachable_iobject_pks,direction,depth,graph_edge_list):


        if direction == 'down':
            # When going down, we need to query for IO2F instances which have one of the
            # specified list of primary keys as primary key of the InfoObject
            # to which the IO2F instance is attached
            # Furthermore, we are only interested into IO2F instances, that constitute a reference,
            # i.e., they contain a Foreignkey to an InfoObject identifier or an InfoObject revision.

            # TODO The part of the query commented out below must be added in once it is decided on how
            # to model references to specific revisions of an InfoObject
            fact_query = Q(iobject_id__in=iobject_pks) & ( ~Q(fact__value_iobject_id=None) )# | ~Q(fact__value_iobject_ts=None))
        else: 
            # When going up, it is the pk of the InfoObject referenced in the IO2F instance that must be contained in the
            # specified list of primary keys

            # TODO The part of the query commented out below must be added in once it is decided on how
            # to model references to specific revisions of an InfoObject

            fact_query = Q(iobject__latest_of__isnull=False) & Q(fact__value_iobject_id__latest__id__in=iobject_pks) #| Q(fact__value_iobject_ts__id__in=iobject_pks)

        if Q_skip_terms:
            # We enrich the query with restrictions upon the fact terms to be considered
            fact_query = ~Q_skip_terms & fact_query


        reference_fact_infos = InfoObject2Fact. \
            objects.filter(fact_query).values_list(*values_list)


        edge_list = []
        hop_node_set = set()

        if direction == 'down':

            for x in reference_fact_infos:
                if x[1]:
                    dest = x[1]
                else:
                    dest = x[2]

                if not keep_graph_info:
                    hop_node_set.add(dest)
                else:

                    edge = {
                        source_label: x[0],
                        '%s_url' % source_label: reverse('url.dingos.view.infoobject', args=[x[0]]),
                        'term': x[3],
                        'attribute': x[4],
                        'fact_node_id': x[5],
                        dest_label : dest,
                        '%s_url' % dest_label: reverse('url.dingos.view.infoobject', args=[dest]),
                        '%s_identifier_ns' % source_label: x[6],
                        '%s_identifier_uid' % source_label: x[7],
                        '%s_name'% source_label: x[8],
                        '%s_iobject_type' % source_label: x[9]
                    }

                    if True: # TODO  second branch once it has been decided on how to model
                             # references to specific revisions of an InfoObject
                        edge['%s_identifier_ns'% dest_label] = x[10]
                        edge['%s_identifier_uid' % dest_label] = x[11]
                        edge['%s_name' % dest_label] = x[12]
                        edge['%s_iobject_type' % dest_label] = x[13]
                    edge_list.append(edge)

        else:
            for x in reference_fact_infos:
                if not keep_graph_info:
                    hop_node_set.add(x[0])
                else:

                    if x[1]:
                        source = x[1]

                    else:
                        source = x[2]

                    edge = {
                        source_label: source,
                        '%s_url' % source_label: reverse('url.dingos.view.infoobject', args=[source]),
                        'term': x[3],
                        'attribute': x[4],
                        'fact_node_id': x[5],
                        dest_label : x[0],
                        '%s_url' % dest_label: reverse('url.dingos.view.infoobject', args=[x[0]]),
                        '%s_identifier_ns' % dest_label: x[6],
                        '%s_identifier_uid' % dest_label: x[7],
                        '%s_name'% dest_label: x[8],
                        '%s_iobject_type'% dest_label: x[9]
                    }

                    if True: # TODO  second branch once it has been decided on how to model
                             # references to specific revisions of an InfoObject
                        edge['%s_identifier_ns' % source_label] = x[10]
                        edge['%s_identifier_uid'% source_label] = x[11]
                        edge['%s_name'% source_label] = x[12]
                        edge['%s_iobject_type' % source_label] = x[13]
                    edge_list.append(edge)


        if keep_graph_info:
            next_hop_iobject_pks = set([x[dest_label] for x in edge_list])


            graph_edge_list = graph_edge_list + edge_list

        else:
            next_hop_iobject_pks = hop_node_set


        if next_hop_iobject_pks.issubset(reachable_iobject_pks) or depth-1 <=0 :
            if keep_graph_info:
                return graph_edge_list
            else:
                return reachable_iobject_pks | next_hop_iobject_pks
        else:
            return follow_references_rec(next_hop_iobject_pks - reachable_iobject_pks,
                                        reachable_iobject_pks | next_hop_iobject_pks,
                                         direction,
                                         depth-1,
                                         graph_edge_list)

    return follow_references_rec(iobject_pks,reachable_iobject_pks,direction,depth,graph_edge_list = [])



