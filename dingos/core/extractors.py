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




from datetime import datetime
from urlparse import urlparse
import StringIO
import json
import csv
from dingos.models import InfoObject2Fact, vIO2FValue
from dingos.core.utilities import set_dict, get_dict
from django.core.urlresolvers import reverse
from dingos.core.utilities import get_from_django_obj
from dingos.graph_traversal import follow_references
from dingos.graph_utils import dfs_preorder_nodes
from dingos import DINGOS_SEARCH_EXPORT_MAX_OBJECTS_PROCESSING

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

    DINGOS_QUERY_ALLOWED_COLUMNS = {}

    DINGOS_QUERY_ALLOWED_COLUMNS['vIO2FValue'] = {
        "object.import_timestamp": ("Import Timestamp", "create_timestamp",[]),
        "object.timestamp": ("Timestamp", "timestamp",[]),
        "object.name": ("Object Name","iobject_name",[]),
        #"identifier": ("Identifier", "identifier",['identifier','identifier__namespace']),
        "object.identifier.uid": ("Identifier UID", "iobject_identifier_uid",[]),
        "object.identifier.namespace": ("Identifier Namespace", "iobject_identifier_uri",[]),
        #"object_type": ("Object Type", "iobject_type",['iobject_type','iobject_type__namespace']),
        "object.object_type.name": ("Object Type (name)", "iobject_type_name",[]),
        #"object_type.namespace": ("Object Type (namespace)", "iobject_type.namespace.uri",['iobject_type__namespace']),
        "object.object_family": ("Object Family", "iobject_family_name",[]),
        "fact.pk": ("Fact PK", "fact_id",[]),
        "value.pk": ("Value PK", "factvalue_id",[]),
        "object.pk": ("Object PK", "iobject_id",[]),
    }


    DINGOS_QUERY_ALLOWED_COLUMNS['InfoObject'] = {
        "import_timestamp": ("Import Timestamp", "create_timestamp",[]),
        "timestamp": ("Timestamp", "timestamp",[]),
        "name": ("Object Name","name",[]),
        "identifier": ("Identifier", "identifier",['identifier','identifier__namespace']),
        "identifier.uid": ("Identifier UID", "identifier.uid",['identifier']),
        "identifier.namespace": ("Identifier Namespace", "identifier.namespace.uri",['identifier__namespace']),
        "object_type": ("Object Type", "iobject_type",['iobject_type','iobject_type__namespace']),
        "object_type.name": ("Object Type (name)", "iobject_type.name",['iobject_type']),
        "object_type.namespace": ("Object Type (namespace)", "iobject_type.namespace.uri",['iobject_type__namespace']),
        "object_family": ("Object Family", "iobject_family.name",['iobject_family']),
        "pk": ("Object PK", "id",[]),
    }

    DINGOS_QUERY_ALLOWED_COLUMNS['InfoObject2Fact'] = {
        "fact_term": ("Fact Term (w/o attribute)","fact.fact_term.term",['fact__fact_term']),
        "fact_term_with_attribute": ("Fact term","fact.fact_term",['fact__fact_term']),
        "value": ("Value","fact.fact_values.value",["fact__fact_values"]),
        "attribute": ("Fact term attribute","fact.fact_term.attribute",['fact__fact_term']),
        "object.import_timestamp": ("Import Timestamp","iobject.create_timestamp",['iobject']),
        "object.timestamp": ("Creation Timestamp","iobject.timestamp",['iobject']),
        "object.identifier.namespace": ("Identifier Namespace","iobject.identifier.namespace.uri",['iobject__identifier__namespace']),
        "object.name": ("Object name","iobject.name",['iobject']),
        "object.object_type.name": ("Object type name","iobject.iobject_type.name",['iobject__iobject_type']),
        "object.object_type.namespace": ("Object type namespace","iobject.iobject_type.namespace.uri",['iobject__iobject_type__namespace']),
        "object.identifier.uid": ("Identifier UID","iobject.identifier.uid",['iobject__identifier']),
        "object.object_family": ("Object Family","iobject.iobject_family",['iobject__iobject_family']),
        "object.identifier": ("Identifier","iobject.identifier",['iobject__identifier','iobject__identifier__namespace']),
        "object.object_type": ("Object Type","iobject.iobject_type",['iobject__iobject_type','iobject__iobject_type__namespace']),
        "fact.pk": ("Fact PK", "fact_id",[]),
        "object.pk": ("Object PK", "id",[]),
    }


    allowed_columns = {}
    enrich_details = True
    format = None
    query_mode = None
    query_mode_restriction = ['InfoObject']

    _default_columns =  [('object.url', 'InfoObject URL'),
        ('exporter','Exporter')]

    exporter_name = None

    def __init__(self,*args,**kwargs):

        self.object_list = kwargs.pop('object_list',[])
        self.io2fs = kwargs.pop('io2f_query',None)
        self.format = kwargs.pop('format',None)
        self.graph = kwargs.pop('graph',None)
        self.package_graph = None
        self.enrich_details = kwargs.pop('enrich_details',self.enrich_details)
        self.query_mode = kwargs.pop('query_mode','InfoObject')

        self._sibling_map = {}

        #self.iobject_map = None

        self.results = []

        self.node_map = None
        self.initialize_object_details()
        self.initialize_allowed_columns()



    def initialize_object_details(self):
        if self.object_list:
            object_count = len(self.object_list)
            if object_count >= DINGOS_SEARCH_EXPORT_MAX_OBJECTS_PROCESSING:
                raise ValueError("Number of objects passed to exporter has reached or surpassed the configured threshold of %s objects" % (DINGOS_SEARCH_EXPORT_MAX_OBJECTS_PROCESSING))
            self.io2fs = self._get_io2fs(map(lambda o:o.pk,list(self.object_list)))
        if self.graph:
            self.io2fs = self._get_io2fs(self.graph.nodes())

        if self.enrich_details:
            #if self.object_list:
            #
            #    self.set_iobject_map()

            if self.graph:

                self._annotate_graph(self.graph)


    def initialize_allowed_columns(self):
        for (col,col_name) in self.default_columns:
            self.allowed_columns[col] = (col_name,col,[])

        self.allowed_columns.update(self.DINGOS_QUERY_ALLOWED_COLUMNS[self.query_mode])

        self.allowed_columns['object.url'] = ('Object URL','_object_url',[])

        self.allowed_columns['package_names'] = ('Package Names','_package_names',[])
        self.allowed_columns['package_urls'] = ('Package URLs','_package_urls',[])




    def init_result_dict(self,obj_or_io2f):
        if isinstance(obj_or_io2f,InfoObject2Fact):
            iobject = None#obj_or_io2f.iobject
            io2f = obj_or_io2f
            io2fv = None
            iobject_pk = io2f.iobject_id
            fact_pk = io2f.fact_id
        elif  isinstance(obj_or_io2f,vIO2FValue):
            iobject = None#obj_or_io2f.iobject
            io2fv = obj_or_io2f
            io2f = None
            iobject_pk = io2fv.iobject_id
            fact_pk = io2fv.fact_id
        else:
            iobject = obj_or_io2f
            iobject_pk = iobject.pk
            io2f = None
            io2fv = None
            fact_pk = None

        result =  {'_object':iobject,
                   '_object_pk':iobject_pk,
                   '_io2f' : io2f,
                   '_io2fv' : io2fv,
                   '_object_url': reverse('url.dingos.view.infoobject', args=[iobject_pk]),
                   }

        if io2f:
            result['_fact_id'] = io2f.fact_id

        if self.exporter_name:
            result['exporter'] = self.exporter_name


        if self.package_graph and iobject_pk:
            # The user also wants info about the packages that contain the object in question
            node_ids = list(dfs_preorder_nodes(self.package_graph, source=iobject_pk))

            package_names = []
            package_urls = []
            for id in node_ids:
                node = self.package_graph.node[id]
                # TODO: Below is STIX-specific and should be factored out
                # by making the iobject type configurable
                if "STIX_Package" in node['iobject_type']:
                    package_names.append(node['name'])
                    package_urls.append(node['url'])
            result['_package_names'] = "| ".join(package_names)
            result['_package_urls'] = "| ".join(package_urls)


        return result



    def additional_calculations(self,columns):
        if 'package_names' in columns or 'package_urls' in columns:
            if not self.package_graph:
                if self.object_list:
                    pks = [one.pk for one in self.object_list]
                else:
                    pks = [one.iobject.pk for one in self.io2fs]
                self.package_graph = follow_references(pks, direction= 'up')


    def export(self,*args,**kwargs):
        #not working if [0] not commented out
        self.override_columns=kwargs.pop('override_columns',[None])#[0]

        if self.override_columns == 'ALL':
            args = self.allowed_columns.keys()
        elif self.override_columns == 'ALMOST_ALL':
            # exclude expensive columns:
            args = set(self.allowed_columns.keys()) - set(['package_urls','package_names'])



        self.additional_calculations(columns=args)

        def recursive_join(xxs, join_string=','):
            if isinstance(xxs, list):
                return join_string.join(map(lambda yys: recursive_join(yys, join_string), xxs))
            else:
                return str(xxs)


        def fill_row(result,columns,mode='json'):

            if self.query_mode == 'InfoObject':
                model_key = '_object'
            elif self.query_mode == 'InfoObject2Fact':
                model_key = '_io2f'
            else:
                model_key = '_io2fv'

            if mode == 'json':
                row = {}
            else:
                row = []
            for column in columns:

                column_key = self.allowed_columns[column][1]
                if column_key in result:
                    column_content = result.get(column_key)
                else:
                    field_components = column_key.split('.')
                    value = get_from_django_obj(result[model_key], field_components)
                    if isinstance(value, list):
                        if len(result) > 1:
                            column_content = recursive_join(value)
                        else:
                            column_content = value[0]
                    else:
                        column_content = value
                if mode == 'json':
                    row[column] = column_content
                else:
                    row.append(column_content)

            return row

        for key in kwargs:
            # This is a hack: the query parser does not remove enclosing quotes
            # from a string argument. So we do it here until this issue is
            # fixed in the query parser

            if kwargs[key][0]=="'":
                kwargs[key]=kwargs[key][1:-1]


        self.extractor(**kwargs)

        if self.format:
            format = self.format
        else:
            format = kwargs.pop('format','json')
        output = []

        if format in ['json','dict']:


            if not args:
                columns = map(lambda x: x[0], self.default_columns)
            else:
                columns = args



            for result in self.results:

                row = fill_row(result,columns,mode='json')
                output.append(row)

            if format == 'json':
                return ('application/json',json.dumps(output,indent=2))
            else:
                return ('',output)
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
                row = fill_row(result,columns,mode='csv')
                writer.writerow(row)

            return('txt',output.getvalue())








    def _get_io2fs(self,object_pks):

        io2fs = vIO2FValue.objects.filter(iobject__id__in=object_pks).order_by('iobject__id','node_id')

        if self.enrich_details:
            io2fs = io2fs.prefetch_related("iobject")

        return io2fs

    def _annotate_graph(self,G):

        last_obj_id = None

        last_io2fv= None

        value_list = []



        current_node = None
        walker = None

        for io2fv in self.io2fs:
            if not current_node or current_node != io2fv.iobject_id:
                current_node = io2fv.iobject_id
                walker = [io2fv]
                G.node[current_node]['facts']=walker
                G.node[current_node]['iobject']=io2fv.iobject
            elif current_node == io2fv.iobject_id:
                walker.append(io2fv)

            if last_io2fv:
                if last_io2fv.node_id == io2fv.node_id and last_obj_id == io2fv.iobject_id:
                    value_list.append(io2fv.value)
                else:
                    last_io2fv.value_list = value_list
                    value_list = []
            last_io2fv = io2fv
            last_obj_id = last_io2fv.iobject_id

            value_list.append(io2fv.value)

        last_io2fv.value_list = value_list


        #self.iobject_map = G.node
        self.object_list = map (lambda x : G.node[x]['iobject'], G.node.keys())


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

                set_dict(self.node_map,io2f,'set_value', io2f.iobject_id, *io2f.node_id.split(':'))

    def get_attributed(self,io2f):
        self.set_node_map()
        node_id = io2f.node_id.split(':')
        results = []
        walker = get_dict(self.node_map,io2f.iobject_id,*node_id[0:-1])

        def get_attributed_rec(walker,results):
            for key in walker:
                if key == '_value':
                    results.append(walker[key])
                else:
                    get_attributed_rec(walker[key],results)

        get_attributed_rec(walker,results)

        return results

    test = 0

    def get_attributes(self,io2f):
        self.set_node_map()
        node_id = io2f.node_id.split(':')
        results = {}

        def get_attributes_rec(node_id,walker,results):
            for child_key in walker:
                if child_key[0] == 'A':
                    if node_id and child_key == node_id[0]:
                        continue
                    else:
                        attribute_io2fv = walker[child_key]['_value']
                        if self.test < 10:
                            self.test += 1
                        set_dict(results, (attribute_io2fv.value,attribute_io2fv.term), 'append', attribute_io2fv.attribute)
            if node_id != []:
                return get_attributes_rec(node_id[1:],walker[node_id[0]],results)
            else:
                return results
        attribute_dict =  get_attributes_rec(node_id,self.node_map[io2f.iobject_id],results)

        for key in attribute_dict:
            attribute_dict[key].reverse()
        return results





    def get_siblings(self,io2f):
        if not self._sibling_map:
            for vio2f in self.io2fs:
                node_id = vio2f.node_id.split(':')
                if node_id:
                    parent_id = ":".join(node_id[0:-1])
                    set_dict(self._sibling_map,vio2f,"append",vio2f.iobject_id,parent_id)


        return self._sibling_map.get(io2f.iobject_id,{}).get(":".join(io2f.node_id.split(':')[0:-1]),[])

class csv_export(InfoObjectDetails):

    exporter_name = 'csv'
    query_mode_restriction = []
    @property
    def  default_columns(self):
        return map(lambda x: (x[0],x[1][0]), self.DINGOS_QUERY_ALLOWED_COLUMNS[self.query_mode].items())

    enrich_details = False
    format = 'csv'
    def extractor(self,**kwargs):
        self.results = []
        if self.object_list:
            for obj in self.object_list:
                self.results.append(self.init_result_dict(obj))
        else:
            for io2f in self.io2fs:
                self.results.append(self.init_result_dict(io2f))


class json_export(InfoObjectDetails):
    exporter_name = 'json'
    @property
    def default_columns(self):
        return map(lambda x: (x[0],x[1][0]), self.DINGOS_QUERY_ALLOWED_COLUMNS[self.query_mode].items())


    query_mode_restriction = []
    enrich_details = False
    format = 'json'
    def extractor(self,**kwargs):

        self.results = []
        if self.object_list:
            for obj in self.object_list:
                self.results.append(self.init_result_dict(obj))
        else:
            for io2f in self.io2fs:
                self.results.append(self.init_result_dict(io2f))


class table_view(InfoObjectDetails):
    @property
    def  default_columns(self):
        return map(lambda x: (x[0],x[1][0]), self.DINGOS_QUERY_ALLOWED_COLUMNS[self.query_mode].items())

    exporter_name = 'table'

    query_mode_restriction = []
    enrich_details = False
    format = 'dict'

    def extractor(self,**kwargs):

        if self.object_list:
            for obj in self.object_list:
                self.results.append(self.init_result_dict(obj))
        else:
            for io2f in self.io2fs:
                self.results.append(self.init_result_dict(io2f))




