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

import re
import json

from django import http
from django.db.models import F
from django.forms.formsets import formset_factory
from braces.views import SuperuserRequiredMixin

from dingos.models import Identifier, InfoObject2Fact, InfoObject, UserData, FactValue, get_or_create_fact

from dingos.filter import InfoObjectFilter, FactTermValueFilter, IdSearchFilter , OrderedFactTermValueFilter
from dingos.forms import EditSavedSearchesForm, EditInfoObjectFieldForm
from dingos import DINGOS_TEMPLATE_FAMILY, DINGOS_INTERNAL_IOBJECT_FAMILY_NAME, DINGOS_USER_PREFS_TYPE_NAME, DINGOS_SAVED_SEARCHES_TYPE_NAME, DINGOS_DEFAULT_SAVED_SEARCHES


from braces.views import LoginRequiredMixin
from view_classes import BasicFilterView, BasicDetailView, BasicTemplateView, BasicListView


class InfoObjectList(BasicFilterView):

    template_name = 'dingos/%s/lists/InfoObjectList.html' % DINGOS_TEMPLATE_FAMILY

    breadcrumbs = (('Dingo',None),
                   ('List',None),
                   ('InfoObject',None))


    filterset_class= InfoObjectFilter

    title = 'List of Info Objects (generic filter)'

    queryset = InfoObject.objects.\
        exclude(latest_of=None). \
        exclude(iobject_family__name__exact=DINGOS_INTERNAL_IOBJECT_FAMILY_NAME). \
        prefetch_related(
        'iobject_type',
        'iobject_type__iobject_family',
        'iobject_family',
        'identifier__namespace',
        'iobject_family_revision',
        'identifier').order_by('-latest_of__pk')
        ### JG/STB: edit for performance
        #'identifier').select_related().distinct().order_by('-latest_of__pk')

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
    template_name = 'dingos/%s/searches/SimpleFactSearch.html' % DINGOS_TEMPLATE_FAMILY

    title = 'Fact-based filtering'


    filterset_class = OrderedFactTermValueFilter
    @property
    def queryset(self):
        if self.get_query_string() == '?':
          queryset = InfoObject2Fact.objects.filter(id=-1)
        else:
           queryset =  InfoObject2Fact.objects.all().\
              exclude(iobject__latest_of=None). \
              exclude(iobject__iobject_family__name__exact=DINGOS_INTERNAL_IOBJECT_FAMILY_NAME). \
              prefetch_related('iobject',
                        'iobject__iobject_type',
                        'fact__fact_term',
                        'fact__fact_values').select_related()#.distinct().order_by('iobject__id')
        return queryset

class UniqueSimpleFactSearch(BasicFilterView):
    template_name = 'dingos/%s/searches/UniqueSimpleFactSearch.html' % DINGOS_TEMPLATE_FAMILY

    title = 'Fact-based filtering (unique)'


    filterset_class = FactTermValueFilter

    
    @property
    def queryset(self):
        if self.get_query_string() == '?':
          queryset = InfoObject2Fact.objects.filter(id=-1)
        else:

          queryset =  InfoObject2Fact.objects.all().\
            exclude(iobject__latest_of=None). \
            exclude(iobject__iobject_family__name__exact=DINGOS_INTERNAL_IOBJECT_FAMILY_NAME). \
            prefetch_related('iobject',
              'iobject__iobject_type',
              'fact__fact_term',
              'fact__fact_values').select_related().order_by('iobject__iobject_type','fact__fact_term','fact__fact_values').distinct('iobject__iobject_type','fact__fact_term','fact__fact_values')
              #'fact__fact_values').select_related().order_by('fact__fact_values__value').distinct('fact__fact_values__value')
        return queryset


    def get_reduced_query_string(self):
        return self.get_query_string(remove=['fact__fact_term','fact__fact_values'])



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

    @property
    def iobject2facts(self):
        return self.object.fact_thru.all().prefetch_related('fact__fact_term',
                                                             'fact__fact_values',
                                                             'fact__fact_values__fact_data_type',
                                                             'fact__value_iobject_id',
                                                             'fact__value_iobject_id__latest',
                                                             'fact__value_iobject_id__latest__iobject_type',
                                                             'node_id')



    template_name = 'dingos/%s/details/InfoObjectDetails.html' % DINGOS_TEMPLATE_FAMILY

    title = 'Info Object Details'

    def get_context_data(self, **kwargs):

        context = super(InfoObjectView_wo_login, self).get_context_data(**kwargs)

        context['show_NodeID'] = self.request.GET.get('show_nodeid',False)
        context['iobject2facts'] = self.iobject2facts
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

            if len(io2f.fact.fact_values.all()) == 1 and io2f.fact.value_iobject_id == None \
                and ( (self.attr_editable and io2f.fact.fact_term.attribute != "") or \
                          not io2f.fact.fact_term.attribute ):
                value_obj = io2f.fact.fact_values.all()[0]
                self.form_builder.append( { 'value' : value_obj.value } )
                self.index.update( { io2f.node_id.name :  (cnt,value_obj) } )
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

        user_data = self.get_user_data()
        self.formset = self.form_class(request.POST.dict())

        if self.formset.is_valid() and request.user.is_authenticated():

            for io2f in self.iobject2facts:
                if io2f.node_id.name in self.index:
                    current_value = self.index[io2f.node_id.name][1]
                    post_value = self.formset.forms[self.index[io2f.node_id.name][0]].cleaned_data['value']

                    if current_value.value != post_value:

                        new_fact,created = get_or_create_fact(io2f.fact.fact_term,
                                                      fact_dt_name=current_value.fact_data_type.name,
                                                      fact_dt_namespace_uri=current_value.fact_data_type.namespace.uri,
                                                      values=[post_value],
                                                      value_iobject_id=None,
                                                      value_iobject_ts=None,
                                                      )
                        io2f.fact = new_fact
                        io2f.save()
                        print io2f.fact

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
        user_data = self.get_user_data()
        saved_searches = user_data['saved_searches'].get('dingos',[])

        initial = []

        counter = 0

        for saved_search in saved_searches:
            initial.append({'new_entry': False,
                            'position' : counter,
                            'title': saved_search['title'],
                            'view' : saved_search['view'],
                            'parameter' : saved_search['parameter']})
            counter +=1
        if self.request.session.get('new_search'):
            initial.append({'position' : counter,
                            'new_entry' : True,
                            'title': "",
                            'view' : self.request.session['new_search']['view'],
                            'parameter' : self.request.session['new_search']['parameter']})
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
                #     }
                #

                if (search['title'] != '' or not search['new_entry']) and not search['DELETE']:
                    dingos_saved_searches.append( { 'view' : search['view'],
                        'parameter' : search['parameter'],
                        'title' : search['title'],
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

