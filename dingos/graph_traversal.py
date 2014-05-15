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


def find_ancestors(iobject_pks,ancestor_iobject_identifier_pks=None,skip_terms=None):

    if not ancestor_iobject_identifier_pks:
        ancestor_iobject_identifier_pks = []

    if not skip_terms:
        skip_terms = [] #[{'term':'','operator':'icontains'},{'attribute':''}]

    skip_term_queries = map(_build_skip_query,skip_terms)

    Q_skip_terms = None

    if len(skip_term_queries) >= 1:
        Q_skip_terms = reduce(lambda x, y : (x & y),skip_term_queries[1:],skip_term_queries[0])

    def find_ancestors_rec(iobject_pks,ancestor_iobject_identifier_pks):

        base_query = Q(facts__value_iobject_id__latest__in=iobject_pks,facts__value_iobject_ts=None)

        if Q_skip_terms:
            child_wo_ts_query = ~Q_skip_term & base_query
        else:
            child_wo_ts_query = base_query

        ancestors = InfoObject. \
            objects.exclude(identifier_id__in=ancestor_iobject_identifier_pks). \
            filter(child_wo_ts_query).prefetch_related('identifier')

        ancestor_info = map(lambda x: (x.pk,x.identifier.pk), ancestors)

        ancestor_identifiers = map(lambda x : x[1],ancestor_info)

        ancestor_objects = map(lambda x : x[0],ancestor_info)

        if ancestor_info == []:
            return ancestor_iobject_identifier_pks
        else:
            return find_ancestors_rec(ancestor_objects, ancestor_iobject_identifier_pks=ancestor_iobject_identifier_pks+ancestor_identifiers)

    return find_ancestors_rec(iobject_pks,ancestor_iobject_identifier_pks)

def find_descendants(iobject_pks,
                     descendant_iobject_pks=None,
                     skip_terms=None):

    if not descendant_iobject_pks:
        descendant_iobject_pks = set()

    if not skip_terms:
        skip_terms = [] #[{'term':'','operator':'icontains'},{'attribute':''}]

    skip_term_queries = map(_build_skip_query,skip_terms)

    Q_skip_terms = None

    if len(skip_term_queries) >= 1:
        Q_skip_terms = reduce(lambda x, y : (x & y),skip_term_queries[1:],skip_term_queries[0])

    def find_descendants_rec(iobject_pks,descendant_iobject_pks):

        if Q_skip_terms:
            child_wo_ts_query = (~(Q_skip_terms | Q(fact__value_iobject_id=None))) & Q(fact__value_iobject_ts=None)
        else:
            child_wo_ts_query = (~Q(fact__value_iobject_id=None)) & Q(fact__value_iobject_ts=None)

        children_wo_timestamp_iobject_pks = InfoObject2Fact. \
            objects.filter(iobject_id__in=iobject_pks). \
            filter(child_wo_ts_query). \
            prefetch_related('iobject__identifier'). \
            values_list('fact__value_iobject_id__latest__pk',flat=True)

        children_wo_timestamp_iobject_pks = set(children_wo_timestamp_iobject_pks)

        if children_wo_timestamp_iobject_pks.issubset(descendant_iobject_pks):
            return descendant_iobject_pks
        else:
            return find_descendants_rec(children_wo_timestamp_iobject_pks - descendant_iobject_pks,
                                        descendant_iobject_pks | children_wo_timestamp_iobject_pks)

    return find_descendants_rec(iobject_pks,descendant_iobject_pks)


def follow_references(iobject_pks,
                      reachable_iobject_pks=None,
                      direction = 'down',
                      skip_terms=None,
                      depth=100000,
                      keep_graph_info=True):

    if not reachable_iobject_pks:
        reachable_iobject_pks = set()

    if not skip_terms:
        skip_terms = [] #[{'term':'','operator':'icontains'},{'attribute':''}]

    skip_term_queries = map(_build_skip_query,skip_terms)

    Q_skip_terms = None

    node_dict = {}

    if len(skip_term_queries) >= 1:
        Q_skip_terms = reduce(lambda x, y : (x & y),skip_term_queries[1:],skip_term_queries[0])

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

                                     #'fact__value_iobject_ts__identifier__namespace__uri',
                                     #'fact__value_iobject_ts__identifier__uid',
                                     #'fact__value_iobject_ts__name',
                                     #'fact__value_iobject_ts__iobject_type__name',
        ]


    def follow_references_rec(iobject_pks,reachable_iobject_pks,direction,depth):


        if direction == 'down':
            fact_query = Q(iobject_id__in=iobject_pks) & ( ~Q(fact__value_iobject_id=None)  | ~Q(fact__value_iobject_ts=None))
        else: # we go up
                                                                            # uncomment below once model has been changed
            fact_query = Q(fact__value_iobject_id__latest__id__in=iobject_pks) #| Q(fact__value_iobject_ts__id__in=iobject_pks)

        if Q_skip_terms:
            fact_query = ~Q_skip_terms & fact_query

        reference_fact_infos = InfoObject2Fact. \
            objects.filter(fact_query).values_list(*values_list)

        print reference_fact_infos

        hop_node_dict = {}
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

                    hop_node_dict[dest] = {'source': x[0],

                    'term': x[3],
                    'attribute': x[4],
                    'fact_node_id': x[5],

                    'source_identifier_ns': x[6],
                    'source_identifier_uid': x[7],
                    'source_name': x[8],
                    'source_iobject_type': x[9],
                    }

                    if True: # TODO  second branch once model has been changed
                        hop_node_dict[dest]['dest_identifier_ns'] = x[10]
                        hop_node_dict[dest]['dest_identifier_uid'] = x[11]
                        hop_node_dict[dest]['dest_name'] = x[12]
                        hop_node_dict[dest]['dest_iobject_type'] = x[13]

        else:
            for x in reference_fact_infos:
                if not keep_graph_info:
                    hop_node_set.add(x[0])
                else:

                    if x[1]:
                        source = x[1]

                    else:
                        source = x[2]

                    hop_node_dict[x[0]] = {'source': source,
                                           'term': x[3],
                                           'attribute': x[4],
                                           'fact_node_id': x[5],

                                           'dest_identifier_ns': x[6],
                                           'dest_identifier_uid': x[7],
                                           'dest_name': x[8],
                                           'dest_iobject_type': x[9],}

                    if True: # TODO  second branch once model has been changed
                        hop_node_dict[x[0]]['source_identifier_ns'] = x[10]
                        hop_node_dict[x[0]]['source_identifier_uid'] = x[11]
                        hop_node_dict[x[0]]['source_name'] = x[12]
                        hop_node_dict[x[0]]['source_iobject_type'] = x[13]


        if keep_graph_info:
            next_hop_iobject_pks = set(hop_node_dict.keys())


            node_dict.update(hop_node_dict)

        else:
            next_hop_iobject_pks = hop_node_set


        if next_hop_iobject_pks.issubset(reachable_iobject_pks) or depth-1 <=0 :
            if keep_graph_info:
                return node_dict
            else:
                return reachable_iobject_pks | next_hop_iobject_pks
        else:
            return follow_references_rec(next_hop_iobject_pks - reachable_iobject_pks,
                                        reachable_iobject_pks | next_hop_iobject_pks,
                                         direction,
                                         depth-1 )

    return follow_references_rec(iobject_pks,reachable_iobject_pks,direction,depth)



