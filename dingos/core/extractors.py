# Copyright (c) Siemens AG, 2013
#
# This file is part of MANTIS.  MANTIS is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either version 2
# of the License, or(at your option) any later version.
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





from urlparse import urlparse
import StringIO
import json
import csv
from dingos.models import InfoObject2Fact
from dingos.core.utilities import set_dict, get_dict
from django.core.urlresolvers import reverse



def extract_fqdn(uri):
    """ Extract the FQDN from an URI."""
    try:
        parsed = urlparse(uri)
        fqdn = parsed.netloc
        return fqdn
    except:
        return None


class InfoObjectDetails(object):
    """
    Given a list of InfoObjects or a graph in which the nodes represent primary keys of
    InfoObjects, this class provides facilities for extracting and exporting detailed
    information. For example usage, have a look into ``postprocessors.py``
    in mantis_stix_importer.

    """

    def __init__(self,*args,**kwargs):
        self.object_list = kwargs.pop('object_list',[])
        self.graph = kwargs.pop('graph',None)

        self.iobject_map = None
        self.io2fs = []
        self.results = []

        self.node_map = None

        if self.object_list:
            self.io2fs = self._get_io2fs(map(lambda o:o.pk,list(self.object_list)))
            self.set_iobject_map()

        elif self.graph:
            self.io2fs = self._get_io2fs(self.graph.nodes())
            self._annotate_graph(self.graph)

    def export(self,*args,**kwargs):

        for key in kwargs:
            # This is a hack: the query parser does not remove enclosing quotes
            # from a string argument. So we do it here until this issue is
            # fixed in the query parser

            if kwargs[key][0]=="'":
                kwargs[key]=kwargs[key][1:-1]


        self.extractor(**kwargs)

        format = kwargs.pop('format','json')
        output = []

        if 'json' in format:

            if not args:
                columns = map(lambda x: x[0], self.default_columns)
            else:
                columns = args



            for result in self.results:

                row = {}
                for column in columns:
                    row[column] = result.get(column,None)
                output.append(row)

            return ('application/json',json.dumps(output,indent=2))
        else: # default csv
            output = StringIO.StringIO()
            writer = csv.writer(output)

            if not args:
                columns = map(lambda x: x[0], self.default_columns)
            else:
                columns = args

            if 'include_column_names' not in kwargs.keys() or kwargs['include_column_names'] != 'False':
                headline = []
                header_dict = dict(self.default_columns)
                for column in columns:
                    headline.append(header_dict.get(column,'UNKNOWN COLUMN'))
                writer.writerow(headline)

            for result in self.results:
                row = []

                for column in columns:
                    row.append(result.get(column,None))
                writer.writerow(row)
            return('txt',output.getvalue())








    def _get_io2fs(self,object_pks):

        io2fs= InfoObject2Fact.objects.filter(iobject__id__in=object_pks).prefetch_related( 'iobject',
                                                                                                'iobject__identifier',
                                                                                                'iobject__identifier__namespace',
                                                                                                'iobject__iobject_family',
                                                                                                'iobject__iobject_type',
                                                                                                'fact__fact_term',
                                                                                                'fact__fact_values',
                                                                                                'fact__fact_values__fact_data_type',
                                                                                                'fact__value_iobject_id',
                                                                                                'fact__value_iobject_id__latest',
                                                                                                'fact__value_iobject_id__latest__iobject_type',
                                                                                                'node_id').order_by('iobject__id','node_id__name')

        return io2fs

    def _annotate_graph(self,G):

        for fact in self.io2fs:
            G.node[fact.iobject.id]['iobject'] = fact.iobject
            if not 'facts' in G.node[fact.iobject.id]:
                G.node[fact.iobject.id]['facts'] = []
            G.node[fact.iobject.id]['facts'].append(fact)

        self.iobject_map = G.node


    def set_iobject_map(self):

        if self.iobject_map == None:
            self.iobject_map = {}
            for io2f in self.io2fs:
                set_dict(self.iobject_map,io2f.iobject,'set', io2f.iobject.id, 'iobject')
                set_dict(self.iobject_map,io2f,'append', io2f.iobject.id,'facts')

            for obj_pk in self.iobject_map:
                node_dict = self.iobject_map[obj_pk]
                try:
                    url = reverse('url.dingos.view.infoobject', args=[obj_pk])
                except:
                    url = None
                node_dict['url'] = url
                node_dict['identifier_ns'] =  node_dict['iobject'].identifier.namespace.uri
                node_dict['identifier_uid'] =  node_dict['iobject'].identifier.uid
                node_dict['name'] = node_dict['iobject'].name
                node_dict['iobject_type'] = node_dict['iobject'].iobject_type.name
                node_dict['iobject_type_family'] = node_dict['iobject'].iobject_type.iobject_family.name



    def set_node_map(self):

        if self.node_map == None:
            self.node_map = {}

            for io2f in self.io2fs:

                set_dict(self.node_map,io2f.fact,'set_value', io2f.iobject.id, *io2f.node_id.name.split(':'))

    def get_attributes(self,io2f):
        self.set_node_map()
        node_id = io2f.node_id.name.split(':')
        results = {}

        def get_attributes_rec(node_id,walker,results):
            for child_key in walker:
                if child_key[0] == 'A':
                    if node_id and child_key == node_id[0]:
                        continue
                    else:
                        attribute_fact = walker[child_key]['_value']
                        set_dict(results, (attribute_fact.fact_values.all()[0].value,attribute_fact.fact_term.term), 'append', attribute_fact.fact_term.attribute)
            if node_id != []:
                return get_attributes_rec(node_id[1:],walker[node_id[0]],results)
            else:
                return results
        attribute_dict =  get_attributes_rec(node_id,self.node_map[io2f.iobject.id],results)

        for key in attribute_dict:
            attribute_dict[key].reverse()
        return results

    def get_siblings(self,io2f):
        self.set_node_map()
        node_id = io2f.node_id.name.split(':')
        results = []
        if node_id:
            parent_id = node_id[0:-1]
            self_id = node_id[-1]


            sibling_dict = get_dict(self.node_map[io2f.iobject.pk],*parent_id)

            if sibling_dict:
                for key in sibling_dict:
                    if key[0] == self_id[0] and key != self_id:
                        sibling = sibling_dict[key].get('_value',None)
                        if sibling:
                            results.append(sibling)
        return results


