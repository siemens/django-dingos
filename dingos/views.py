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

import json
import re
from django import http
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import F
from django.forms.formsets import formset_factory
from django.shortcuts import get_object_or_404
from django.views.generic import RedirectView


from django.contrib import messages
from django.db import DataError
from django.core.exceptions import FieldError
from django.contrib.auth.models import User

from provider.oauth2.models import Client

from braces.views import SuperuserRequiredMixin

from dingos.models import InfoObject2Fact, InfoObject, UserData, vIO2FValue, get_or_create_fact, Fact, dingos_class_map
from dingos.view_classes import BasicJSONView, POSTPROCESSOR_REGISTRY
from dingos.core.utilities import listify

import csv

from dingos.filter import InfoObjectFilter, CompleteInfoObjectFilter,FactTermValueFilter, IdSearchFilter , OrderedFactTermValueFilter
from dingos.forms import EditSavedSearchesForm, EditInfoObjectFieldForm, OAuthInfoForm, OAuthNewClientForm

from dingos import DINGOS_TEMPLATE_FAMILY, \
    DINGOS_INTERNAL_IOBJECT_FAMILY_NAME, \
    DINGOS_USER_PREFS_TYPE_NAME, \
    DINGOS_SAVED_SEARCHES_TYPE_NAME, \
    DINGOS_DEFAULT_SAVED_SEARCHES, \
    DINGOS_OBJECTTYPE_VIEW_MAPPING, \
    DINGOS_INFOOBJECT_GRAPH_TYPES

from braces.views import LoginRequiredMixin
from view_classes import BasicFilterView, BasicDetailView, BasicTemplateView, BasicListView, BasicCustomQueryView, processTagging
from queryparser.queryparser import QueryParser
from queryparser.querylexer import QueryLexerException
from queryparser.querytree import FilterCollection, QueryParserException
import importlib


from dingos.graph_traversal import follow_references

from dingos.core.utilities import match_regex_list

def getTags(objects,complex=False,model=None):
    """
    :param objects: single/multiple objects or object pks as list or set
    :param complex: iobject and fact tags if set to True
    :param model: type of objects have to be provided if using object pks
    :return: dict like following:

    { <IObjectPK> ; { 'tags' : [<list of tags on current IObject>],
                      <FactPK> : [<list of tags on current Fact>],
                      ...
                    }
    }
    """
    tag_map = {}
    if isinstance(objects,set):
        objects = list(objects)
    objects = listify(objects)

    def _simple_q(_objects,model):
        if not model:
            model = type(_objects[0])
        obj_pks = objects if isinstance(objects[0],int) else set([x.id for x in objects])
        cols = ['id','tag_through__tag__name']
        tags_q = model.objects.filter(id__in = obj_pks).filter(tag_through__isnull=False).values(*cols)
        return tags_q

    if complex:
        #filter(fact__tag_through__isnull=False) workarround to achieve INNER JOIN
        cols = ['identifier_id','fact_id','fact__tag_through__tag__name']
        ident_pks_q = list(_simple_q(objects,model=model))
        ident_pks = objects if model else set([x.id for x in objects])
        fact_tags_q = list(vIO2FValue.objects.filter(identifier_id__in = ident_pks).filter(fact__tag_through__isnull=False).values(*cols))
        tag_map = {}
        for tag in ident_pks_q:
            ident = tag_map.setdefault(tag['id'],{})
            tags = ident.setdefault('tags',[])
            tags.append(tag['tag_through__tag__name'])
        for tag in fact_tags_q:
            ident = tag_map.setdefault(tag['identifier_id'],{})
            fact = ident.setdefault(tag['fact_id'],[])
            fact.append(tag['fact__tag_through__tag__name'])

    else:
        tags_q = _simple_q(objects,model=model)
        for tag in tags_q:
            tag_list = tag_map.setdefault(tag['id'],[])
            tag_list.append(tag['tag_through__tag__name'])

    return tag_map

class InfoObjectList(BasicFilterView):


    exclude_internal_objects = True

    template_name = 'dingos/%s/lists/InfoObjectList.html' % DINGOS_TEMPLATE_FAMILY

    breadcrumbs = (('Dingo',None),
                   ('List',None),
                   ('InfoObject',None))


    fields_for_api_call = ['identifier','timestamp','import_timestamp','name','object_type','package_names','package_urls']

    filterset_class= InfoObjectFilter

    title = 'List of Info Objects (generic filter)'

    @property
    def queryset(self):
        queryset = InfoObject.objects.\
            exclude(latest_of=None)

        if self.exclude_internal_objects:
            queryset = queryset.exclude(iobject_family__name__exact=DINGOS_INTERNAL_IOBJECT_FAMILY_NAME)

        queryset = queryset.prefetch_related(
            'iobject_type',
            'iobject_type__iobject_family',
            'iobject_family',
            'identifier__namespace',
            'iobject_family_revision',
            'identifier').order_by('-latest_of__pk')
        return queryset

class InfoObjectListIncludingInternals(SuperuserRequiredMixin,InfoObjectList):

    counting_paginator = False

    filterset_class= CompleteInfoObjectFilter

    exclude_internal_objects=False

class InfoObjectList_Id_filtered(BasicFilterView):

    template_name = 'dingos/%s/lists/InfoObjectList.html' % DINGOS_TEMPLATE_FAMILY

    breadcrumbs = (('Dingo',None),
                   ('List',None),
                   ('InfoObject',None))

    filterset_class= IdSearchFilter

    title = 'ID-based filtering'

    queryset = InfoObject.objects.exclude(latest_of=None). \
        exclude(iobject_family__name__exact=DINGOS_INTERNAL_IOBJECT_FAMILY_NAME). \
        prefetch_related(
        'iobject_type',
        'iobject_family',
        'iobject_family_revision',
        'identifier').select_related().distinct().order_by('-latest_of__pk')

class InfoObjectsEmbedded(BasicListView):
    template_name = 'dingos/%s/lists/InfoObjectEmbedded.html' % DINGOS_TEMPLATE_FAMILY

    breadcrumbs = (('Dingo',None),
                   ('List',None),
                   ('InfoObject',None))

    filterset_class = InfoObjectFilter

    @property
    def title(self):
        return 'Objects that embed object "%s" (id %s)' % (self.iobject.name,
                                                           self.iobject.identifier)
    @property
    def iobject(self):
        return InfoObject.objects.get(pk=int(self.kwargs['pk']))

    def get_queryset(self):

        queryset = InfoObject2Fact.objects.exclude(iobject__latest_of=None). \
            filter(fact__value_iobject_id__id=self.iobject.identifier.id). \
            filter(iobject__timestamp=F('iobject__identifier__latest__timestamp')). \
            order_by('-iobject__timestamp')
        return queryset

    def get_context_data(self, **kwargs):
        context = super(InfoObjectsEmbedded, self).get_context_data(**kwargs)
        context['iobject'] = self.iobject
        return context

class SimpleFactSearch(BasicFilterView):

    counting_paginator = False

    template_name = 'dingos/%s/searches/SimpleFactSearch.html' % DINGOS_TEMPLATE_FAMILY

    title = 'Fact-based filtering'

    filterset_class = OrderedFactTermValueFilter

    fields_for_api_call = ['object.name','object.object_type','fact_term_with_attribute','value','package_names','package_urls']

    @property
    def queryset(self):
        if self.get_query_string() == '?':
          queryset = InfoObject2Fact.objects.filter(id=-1)
        else:
           queryset =  InfoObject2Fact.objects.all().\
              exclude(iobject__latest_of=None). \
              exclude(iobject__iobject_family__name__exact=DINGOS_INTERNAL_IOBJECT_FAMILY_NAME)

           queryset = queryset.\
              prefetch_related('iobject',
                        'iobject__iobject_type',
                        'fact__fact_term',
                        'fact__fact_values').select_related()#.distinct().order_by('iobject__id')
        return queryset

class UniqueSimpleFactSearch(BasicFilterView):

    counting_paginator = False

    template_name = 'dingos/%s/searches/UniqueSimpleFactSearch.html' % DINGOS_TEMPLATE_FAMILY

    title = 'Fact-based filtering (unique)'

    fields_for_api_call = ['object.object_type','fact_term_with_attribute','value']

    filterset_class = FactTermValueFilter


    @property
    def queryset(self):
        if self.get_query_string() == '?':
          queryset = InfoObject2Fact.objects.filter(id=-1)
        else:

          queryset =  InfoObject2Fact.objects.all().\
            exclude(iobject__latest_of=None). \
            exclude(iobject__iobject_family__name__exact=DINGOS_INTERNAL_IOBJECT_FAMILY_NAME). \
            order_by('iobject__iobject_type','fact__fact_term','fact__fact_values').distinct('iobject__iobject_type','fact__fact_term','fact__fact_values')

          queryset = queryset.\
            prefetch_related('iobject',
              'iobject__iobject_type',
              'fact__fact_term',
              'fact__fact_values').select_related()

        return queryset


    def get_reduced_query_string(self):
        return self.get_query_string(remove=['fact__fact_term','fact__fact_values','page'])

class InfoObjectRedirect(RedirectView):

    permanent = False

    @property
    def pattern_name(self):
        object = get_object_or_404(InfoObject, pk=self.kwargs['pk'])

        iobject_type_name = object.iobject_type.name
        iobject_type_family_name = object.iobject_family.name



        object_specific_view = DINGOS_OBJECTTYPE_VIEW_MAPPING.get(iobject_type_family_name,{}). \
                                      get(iobject_type_name)

        if object_specific_view:
            return object_specific_view
        else:
            return 'url.dingos.view.infoobject.standard'

class InfoObjectView_wo_login(BasicDetailView):
    """
    View for viewing an InfoObject.

    Note that below we generate a query set for the facts by hand
    rather than carrying out the queries through the object-query.
    This is because the prefetch_related
    is treated leads to a prefetching of *all* facts, even though
    pagination only displays 100 or 200 or so.
    """

    # Config for Prefetch/SelectRelated Mixins_
    select_related = ()
    prefetch_related = ('iobject_type',
                        'iobject_type__namespace',
                        'identifier__namespace',
    )

    breadcrumbs = (('Dingo',None),
                   ('View',None),
                   ('InfoObject','url.dingos.list.infoobject.generic'),
                   ('[RELOAD]',None)
    )
    model = InfoObject

    template_name = 'dingos/%s/details/InfoObjectDetails.html' % DINGOS_TEMPLATE_FAMILY

    title = 'Info Object Details'

    show_datatype = False


    @property
    def iobject2facts(self):
        # TODO: The vIO2FValue view is such that empty objects lead to entries with no fact info in them ..., 
        # which leads to problems below -- here we get rid of such spurious lines by checking above node_id__isnull=False
        facts_in_obj =  vIO2FValue.objects.filter(iobject=self.object.id,node_id__isnull=False).order_by('node_id')

        value_list = []
        last_obj = None
        for fact in facts_in_obj:
            if last_obj:
                if last_obj.node_id == fact.node_id:
                    value_list.append(fact.value)
                else:
                    last_obj.value_list = value_list
                    value_list = []
            last_obj = fact
            value_list.append(fact.value)
        if last_obj:
            last_obj.value_list = value_list

        facts_in_obj = [x for x in facts_in_obj if 'value_list' in dir(x)]

        return facts_in_obj

        #return self.object.fact_thru.all().prefetch_related(
        #    'fact__fact_term',
        #    'fact__fact_values',
        #    'fact__fact_values__fact_data_type',
        #    'fact__value_iobject_id',
        #    'fact__value_iobject_id__latest',
        #    'fact__value_iobject_id__latest__iobject_type',
        #    'node_id')



    #def graph_iobject2facts(self):
    #    obj_pk = self.object.id
    #    graph = InfoObject.annotated_graph([obj_pk])
    #    edges_from_top = graph.edges(nbunch=[obj_pk], data = True)

    #    indicators =  [e[1] for e in edges_from_top if "Indicator" in e[2]['term'][0]]


    #    return graph.node[indicators[0]]['facts']




    template_name = 'dingos/%s/details/InfoObjectDetails.html' % DINGOS_TEMPLATE_FAMILY

    title = 'Info Object Details'

    def get_context_data(self, **kwargs):

        context = super(InfoObjectView_wo_login, self).get_context_data(**kwargs)

        context['show_datatype'] = self.request.GET.get('show_datatype',False)
        context['show_NodeID'] = self.request.GET.get('show_nodeid',False)
        context['iobject2facts'] = self.iobject2facts

        if self.__class__ == InfoObjectView:
            context['tag_dict'] = getTags(self.object.identifier,complex=True)

        context['io2fvs'] = None
        try:
            context['highlight'] = self.request.GET['highlight']
        except KeyError:
            context['highlight'] = None

        return context

class InfoObjectView(LoginRequiredMixin,InfoObjectView_wo_login):
    """
    View for viewing an InfoObject.
    """

    pass

class BasicInfoObjectEditView(LoginRequiredMixin,InfoObjectView_wo_login):
    """
    Attention: this view overwrites an InfoObject without creating
    a new revision. It is currently only used for editing the
    UserConfigs or for edits carried out by the superuser.
    """
    template_name = 'dingos/%s/edits/InfoObjectsEdit.html' % DINGOS_TEMPLATE_FAMILY
    title = 'Edit Info Object Details'

    attr_editable = False # set to True to also allow editing of attributes

    # we use a formset to deal with a varying number of forms

    form_class = formset_factory(EditInfoObjectFieldForm, extra=0)



    index = {}
    form_builder = []

    def build_form(self):

        self.form_builder = []
        self.index = {}
        cnt = 0

        for io2f in self.iobject2facts:

            if len(io2f.value_list) == 1 and not io2f.referenced_iobject_identifier_id  \
                and ( (self.attr_editable and io2f.attribute != "") or \
                          not io2f.attribute ):

                self.form_builder.append( { 'value' : io2f.value_list[0] } )
                self.index.update( { io2f.node_id :  (cnt,io2f) } )
                cnt += 1



    def get_context_data(self, **kwargs):
        context = super(InfoObjectView_wo_login, self).get_context_data(**kwargs)
        context.update(super(LoginRequiredMixin, self).get_context_data(**kwargs))

        self.build_form()

        context['formset'] = self.form_class(initial=self.form_builder)
        context['formindex'] = self.index


        return context

    def get(self, request, *args, **kwargs):

        return super(InfoObjectView_wo_login,self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        super(InfoObjectView_wo_login,self).get(request, *args, **kwargs)
        self.build_form()

        print self.index
        user_data = self.get_user_data()
        self.formset = self.form_class(request.POST.dict())

        if self.formset.is_valid() and request.user.is_authenticated():

            for io2fv in self.iobject2facts:
                if io2fv.node_id in self.index:
                    io2f = io2fv.io2f
                    current_value = self.index[io2fv.node_id][1]
                    post_value = self.formset.forms[self.index[io2fv.node_id][0]].cleaned_data['value']


                    if current_value.value_list[0] != post_value:

                        new_fact,created = get_or_create_fact(io2fv.fact.fact_term,
                                                      fact_dt_name=current_value.fact_data_type.name,
                                                      fact_dt_namespace_uri=current_value.fact_data_type.namespace.uri,
                                                      values=[post_value],
                                                      value_iobject_id=None,
                                                      value_iobject_ts=None,
                                                      )
                        io2f.fact = new_fact
                        io2f.save()

        return super(InfoObjectView_wo_login,self).get(request, *args, **kwargs)

class InfoObjectEditView(SuperuserRequiredMixin,BasicInfoObjectEditView):
    """
    Attention: this view overwrites an InfoObject without creating
    a new revision. It is currently only used for editing the
    UserConfigs or for edits carried out by the superuser.
    """
    pass

class UserPrefsView(BasicInfoObjectEditView):
    """
    View for editing the user configuration of a user.
    """

    def get_object(self):
        # We delete the session data in  order to achieve a reload
        # when viewing this page.




        try:
            del(self.request.session['customization'])
            del(self.request.session['customization_for_authenticated'])
        except KeyError, err:
            pass
        return UserData.get_user_data_iobject(user=self.request.user,data_kind=DINGOS_USER_PREFS_TYPE_NAME)

class CustomSearchesEditView(BasicTemplateView):
    """
    View for editing the saved searches of a user.
    """

    template_name = 'dingos/%s/edits/SavedSearchesEdit.html' % DINGOS_TEMPLATE_FAMILY
    title = 'Saved searches'

    form_class = formset_factory(EditSavedSearchesForm, can_order=True, can_delete=True,extra=0)
    formset = None

    def get_context_data(self, **kwargs):
        context = super(CustomSearchesEditView, self).get_context_data(**kwargs)

        context['formset'] = self.formset

        return context

    def get(self, request, *args, **kwargs):
        user_data = self.get_user_data(load_new_settings=True)
        saved_searches = user_data['saved_searches'].get('dingos',[])

        initial = []

        counter = 0

        for saved_search in saved_searches:
            # TODO: there is an error either in core.datatypes.from_flat_repr or
            # (more likely) in the Mixin that retrieves the user data, which turns
            # empty values into {}. The statements below remove this
            # spurious '{}'.

            if saved_search['title'] == {}:
                saved_search['title']= ''

            if saved_search.get('identifier') == {}:
                saved_search['identifier']= ''

            if saved_search.get('custom_query',{}) == {}:
                saved_search['custom_query']= ''



            initial.append({'new_entry': False,
                            'position' : counter,
                            'title': saved_search['title'],
                            'identifier': saved_search.get('identifier'),
                            'view' : saved_search['view'],
                            'parameter' : saved_search['parameter'],
                            'custom_query': saved_search.get('custom_query','')})
            counter +=1
        if self.request.session.get('new_search'):
            initial.append({'position' : counter,
                            'new_entry' : True,
                            'title': "",
                            'identifier':"",
                            'view' : self.request.session['new_search']['view'],
                            'parameter' : self.request.session['new_search']['parameter'],
                            'custom_query' : self.request.session['new_search'].get('custom_query','')
            })
            del(self.request.session['new_search'])
            self.request.session.modified = True

        self.formset = self.form_class(initial=initial)
        return super(BasicTemplateView,self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):

        user_data = self.get_user_data()
        self.formset = self.form_class(request.POST.dict())
        saved_searches = user_data['saved_searches']


        if self.formset.is_valid() and request.user.is_authenticated():
            dingos_saved_searches = []

            for form in self.formset.ordered_forms:
                search = form.cleaned_data
                # Search has the following form::
                #
                #     {'view': u'url.dingos.list.infoobject.generic',
                #      'parameter': u'iobject_type=72',
                #      u'ORDER': None,
                #      u'DELETE': False,
                #     'title': u'Filter for STIX Packages'
                #     'identifier': u'all_stix_packages'
                #     }
                #

                if (search['title'] != '' or not search['new_entry']) and not search['DELETE']:
                    dingos_saved_searches.append( { 'view' : search['view'],
                                                    'parameter' : search['parameter'],
                                                    'custom_query' : search.get('custom_query',''),
                                                    'title' : search['title'],
                                                    'identifier' : search['identifier'],
                                                    }
                    )

            saved_searches['dingos'] = dingos_saved_searches
            UserData.store_user_data(user=request.user,
                                     data_kind=DINGOS_SAVED_SEARCHES_TYPE_NAME,
                                     user_data=saved_searches,
                                     iobject_name = "Saved searches of user '%s'" % request.user.username)

            # enforce reload of session
            del request.session['customization']
            request.session.modified = True

        else:
            # Form was not valid, we return the form as is

            return super(BasicTemplateView,self).get(request, *args, **kwargs)

        return self.get(request, *args, **kwargs)

class InfoObjectJSONView(BasicDetailView):
    """
    View for JSON representation of InfoObjects.
    """

    select_related = ()
    prefetch_related = () # The to_dict function itself defines the necessary prefetch_stuff

    model = InfoObject

    def render_to_response(self, context):
        #return self.get_json_response(json.dumps(context['object'].show_elements(""),indent=2))
        include_node_id = self.request.GET.get('include_node_id',False)

        return self.get_json_response(json.dumps(context['object'].to_dict(include_node_id=include_node_id,track_namespaces=True),indent=2))

    def get_json_response(self, content, **httpresponse_kwargs):
        return http.HttpResponse(content,
                                 content_type='application/json',
                                 **httpresponse_kwargs)

class CustomInfoObjectSearchView(BasicCustomQueryView):
    #list_actions = [ ('Share', 'url.dingos.action_demo', 0),
    #                 ('Do something else', 'url.dingos.action_demo', 0),
    #                 ('Or yet something else', 'url.dingos.action_demo', 2),
    #                  ]

    pass

class CustomFactSearchView(BasicCustomQueryView):


    template_name = 'dingos/%s/searches/CustomFactSearch.html' % DINGOS_TEMPLATE_FAMILY
    title = 'Custom Fact Search'

    distinct = ('iobject__iobject_type', 'fact__fact_term', 'fact__fact_values')

    query_base = InfoObject2Fact.objects

    col_headers = ["IO-Type", "Fact Term", "Value"]
    selected_cols = ["iobject.iobject_type.name", "fact.fact_term", "fact.fact_values.all"]

    prefetch_related = ('iobject',
                        'iobject__iobject_type',
                        'fact__fact_term',
                        'fact__fact_values',
                        'fact__fact_values__fact_data_type',
                        'fact__value_iobject_id',
                        'fact__value_iobject_id__latest',
                        'fact__value_iobject_id__latest__iobject_type',
                        'node_id')

class InfoObjectExportsView(BasicTemplateView):
    # When building the graph, we skip references to the kill chain. This is because
    # in STIX reports where the kill chain information is consistently used, it completly
    # messes up the graph display.

    skip_terms = [
        # We do not want to follow 'Related Object' links and similar
        {'term':'Related','operator':'icontains'},
        ]

    max_objects = None


    def get(self,request,*args,**kwargs):

        api_test = 'api_call' in request.GET



        iobject_id = self.kwargs.get('pk', None)

        graph= follow_references([iobject_id],
                                 skip_terms = self.skip_terms,
                                 direction='down',
                                 max_nodes=self.max_objects,
                                 )


        exporter = self.kwargs.get('exporter', None)


        if exporter in POSTPROCESSOR_REGISTRY:

            postprocessor_class = POSTPROCESSOR_REGISTRY[exporter]

            postprocessor = postprocessor_class(graph=graph,
                                                query_mode='vIO2FValue',
                                                )


            if 'columns' in self.request.GET:
                columns = self.request.GET.get('columns')
                columns = map(lambda x: x.strip(),columns.split(','))

            else:
                columns = []

            (content_type,result) = postprocessor.export(*columns,**self.request.GET)




        else:
            content_type = None
            result = 'NO EXPORTER %s DEFINED' % exporter

        if api_test:
            self.api_result = result
            self.api_result_content_type = content_type
            self.template_name = 'dingos/%s/searches/API_Search_Result.html' % DINGOS_TEMPLATE_FAMILY
            return super(InfoObjectExportsView, self).get(request, *args, **kwargs)
        else:
            response = HttpResponse(content_type=content_type)
            response.write(result)
            return response

class InfoObjectExportsViewWithTagging(BasicListView):
    template_name = 'dingos/%s/lists/ExportFactList.html' % DINGOS_TEMPLATE_FAMILY

    list_actions = [
                ('Tag', 'url.dingos.action.add_tagging', 0),
            ]

    skip_terms = [
        # We do not want to follow 'Related Object' links and similar
        {'term':'Related','operator':'icontains'},
        ]

    #max nodes to discover by graph building (follow references)
    max_objects = None

    fact_ids = []

    @property
    def queryset(self):
        queryset = Fact.objects.filter(id__in=self.fact_ids)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(InfoObjectExportsViewWithTagging, self).get_context_data(**kwargs)
        return context

    def get(self,request,*args,**kwargs):
        iobject_id = self.kwargs.get('pk', None)

        graph= follow_references([iobject_id],
                                 skip_terms = self.skip_terms,
                                 direction='down',
                                 max_nodes=self.max_objects,
                                 )

        exporter = self.kwargs.get('exporter', None)

        if exporter in POSTPROCESSOR_REGISTRY:
            postprocessor_class = POSTPROCESSOR_REGISTRY[exporter]
            postprocessor = postprocessor_class(graph=graph,
                                                query_mode='vIO2FValue',
                                                )

            if 'columns' in self.request.GET:
                columns = self.request.GET.get('columns')
                columns = map(lambda x: x.strip(),columns.split(','))

            else:
                columns = []

            kwargs = {'format' : 'dict'}
            kwargs.update(self.request.GET)
            (content_type,result) = postprocessor.export(*columns,**kwargs)

        else:
            result = 'NO EXPORTER %s DEFINED' % exporter

        self.result = result
        self.fact_ids = []
        for x in result:
            x['fact.pk'] = int(x['fact.pk'])
            self.fact_ids.append(x['fact.pk'])

        return super(InfoObjectExportsViewWithTagging, self).get(request, *args, **kwargs)

class InfoObjectJSONGraph(BasicJSONView):
    """
    View for JSON representation of InfoObjects Graph data.
    Used in the front-end detail view to display a reference graph of the current InfoObject
    """

    # When building the graph, we skip references to the kill chain. This is because
    # in STIX reports where the kill chain information is consistently used, it completly
    # messes up the graph display.

    skip_terms = [
        # The kill chain links completely mess up the graph
        {'attribute':'kill_chain_id'},
        {'term':'Kill_Chain','operator':'icontains'},
        {'term':'KillChain','operator':'icontains'},
        ]


    @property
    def returned_obj(self):
        res = {
            'status': False,
            'msg': 'An error occured.',
            'data': None
        }


        iobject_id = self.kwargs.get('pk', None)
        if not iobject_id:
            POST = self.request.POST
            iobject_id = POST.get('iobject_id', None)

        iobject = InfoObject.objects.all().filter(pk=iobject_id)[0]
        graph_mode = None
        for graph_type in DINGOS_INFOOBJECT_GRAPH_TYPES:
            family_pattern = graph_type['info_object_family_re']
            type_pattern = graph_type['info_object_type_re']
            family = str(iobject.iobject_family)
            type = str(iobject.iobject_type)
            if re.match(family_pattern, family) and re.match(type_pattern, type):
                available_modes = graph_type['available_modes']
                res['available_modes'] = available_modes

                graph_mode=None
                default_mode=None

                mode_key = self.request.GET.get('mode',graph_type['default_mode'])

                for mode in available_modes:
                    if mode.get('mode_key')==mode_key:
                        graph_mode = mode
                        break
                    elif mode.get('mode_key')== graph_type['default_mode']:
                        default_mode = mode

                if not graph_mode:
                    graph_mode = default_mode

                res['msg'] = graph_mode['title']
                break


        #graph = follow_references([iobject_id],
        #                          skip_terms = self.skip_terms,
        #                          direction='up',
        #                          reverse_direction=True,
        #                          max_nodes=self.max_objects)

        graph=follow_references([iobject_id],
                                skip_terms = self.skip_terms,
                                **graph_mode['traversal_args'])

        # Graph postprocessing

        if 'postprocessor' in graph_mode:
            postprocessor_path = graph_mode['postprocessor']
            try:
                postprocessor_module = importlib.import_module(postprocessor_path)
                postprocessor = getattr(postprocessor_module, "process")
                graph = postprocessor(graph)
            except:
                pass

        if iobject_id:
            res['status'] = True

            if graph.graph['max_nodes_reached']:
                res['msg'] = res['msg'] + " (partial, %s InfoObjects)" % graph_mode['traversal_args'].get('max_nodes','??')

            # test-code for showing only objects and their relations
            #nodes_to_remove = []
            #for (n,d) in graph.nodes(data=True):
            #    if not 'Object' in d['iobject_type']:
            #        nodes_to_remove.append(n)
            #graph.remove_nodes_from(nodes_to_remove)

            res['data'] = {
                'node_id': iobject_id,
                'nodes': graph.nodes(data=True),
                'edges': graph.edges(data=True),
            }

        return res

class OAuthInfo(BasicTemplateView):
    """
    View for editing the OAuth information.
    """

    template_name = 'dingos/%s/edits/OAuthInfoEdit.html' % DINGOS_TEMPLATE_FAMILY
    title = 'Edit OAuth Keys'

    form_class = formset_factory(OAuthInfoForm, can_order=True, can_delete=True, extra=0)
    formset = None

    def get_context_data(self, **kwargs):
        context = super(OAuthInfo, self).get_context_data(**kwargs)
        context['formset'] = self.formset
        context['newclientform'] = OAuthNewClientForm
        return context

    def get(self, request, *args, **kwargs):
        initial = []

        # Show all client key pairs for the current user
        user = User.objects.get(username=request.user.username)

        # Insert test clients
        #for counter in range(10):
        #    Client(user=user, name="Testclient" + str(counter), client_type=1).save()

        clients = Client.objects.all().filter(user=user)
        for client in clients:
            initial.append({"client_name": client.name,
                            "client_id": client.client_id,
                            "client_secret": client.client_secret})

        self.formset = self.form_class(initial=initial)
        return super(BasicTemplateView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        initial = []
        self.formset = self.form_class(request.POST.dict())
        if self.formset.is_valid() and request.user.is_authenticated():
            user = User.objects.get(username=request.user.username)

            if "generate_new_client" in request.POST:
                client_name = request.POST.dict()["new_client"]
                client = Client(user=user, name=client_name, client_type=1)
                client.save()
            elif 'update_clients' in request.POST:
                # TODO It would be better to update the existing clients instead of delete&insert
                # Delete all clients
                clients = Client.objects.all().filter(user=user)
                for client in clients:
                    client.delete()

                # Insert all clients again
                self.formset.ordered_forms.reverse()
                for form in self.formset.ordered_forms:
                    client = Client(user=user,
                                    name=form.cleaned_data["client_name"],
                                    client_id=form.cleaned_data["client_id"],
                                    client_secret=form.cleaned_data["client_secret"],
                                    client_type=1)
                    client.save()

            # Initialize client page
            clients = Client.objects.all().filter(user=user)
            for client in clients:
                initial.append({"client_name": client.name,
                                "client_id": client.client_id,
                                "client_secret": client.client_secret})

            self.formset = self.form_class(initial=initial)
        return super(BasicTemplateView, self).get(request, *args, **kwargs)

class TaggingJSONView(BasicJSONView):
    @property
    def returned_obj(self):
        if self.request.is_ajax() and self.request.method == 'POST' and self.request.user.is_authenticated():
            data = json.loads(self.request.body)
            action = self.kwargs.get('action','')
            obj_pks = data.get('objects',[])
            type = data.get('type','')
            tag_name = data.get('tag','')
            if action and obj_pks and type and tag_name:
                return processTagging(action,obj_pks,type,tag_name,self.request.user)
        return {}