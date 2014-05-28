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

from dingos.models import InfoObject2Fact, InfoObject


def _build_skip_query(skip_info):
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
                      reachable_iobject_pks=None,
                      direction = 'down',
                      skip_terms=None,
                      depth=100000,
                      keep_graph_info=True,
                      reverse=False):

    if not reverse:
        source_label = 'source'
        dest_label = 'dest'
    else:
        source_label = 'dest'
        dest_label = 'source'

    if not reachable_iobject_pks:
        reachable_iobject_pks = set()

    if not skip_terms:
        skip_terms = []

    skip_term_queries = map(_build_skip_query,skip_terms)

    Q_skip_terms = None



    if len(skip_term_queries) >= 1:
        Q_skip_terms = reduce(lambda x, y : (x | y),skip_term_queries[1:],skip_term_queries[0])

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


    def follow_references_rec(iobject_pks,reachable_iobject_pks,direction,depth,graph_edge_list):


        if direction == 'down':
            fact_query = Q(iobject_id__in=iobject_pks) & ( ~Q(fact__value_iobject_id=None)  | ~Q(fact__value_iobject_ts=None))
        else: # we go up
                                                                            # uncomment below once model has been changed
            fact_query = Q(iobject__latest_of__isnull=False) & Q(fact__value_iobject_id__latest__id__in=iobject_pks) #| Q(fact__value_iobject_ts__id__in=iobject_pks)

        if Q_skip_terms:
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

                    edge = {source_label: x[0],

                    'term': x[3],
                    'attribute': x[4],
                    'fact_node_id': x[5],
                    dest_label : dest,
                    '%s_identifier_ns' % source_label: x[6],
                    '%s_identifier_uid' % source_label: x[7],
                    '%s_name'% source_label: x[8],
                    '%s_iobject_type' % source_label: x[9],
                    }

                    if True: # TODO  second branch once model has been changed
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

                    edge = {source_label: source,
                            'term': x[3],
                            'attribute': x[4],
                            'fact_node_id': x[5],
                            dest_label : x[0],
                            '%s_identifier_ns' % dest_label: x[6],
                            '%s_identifier_uid' % dest_label: x[7],
                            '%s_name'% dest_label: x[8],
                            '%s_iobject_type'% dest_label: x[9],}

                    if True: # TODO  second branch once model has been changed
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



