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

from dingos.models import Identifier, InfoObject2Fact, InfoObject, UserData
from dingos.filter import InfoObjectFilter, FactTermValueFilter, IdSearchFilter
from dingos.forms import EditSavedSearchesForm
from dingos import DINGOS_TEMPLATE_FAMILY, DINGOS_INTERNAL_IOBJECT_FAMILY_NAME, DINGOS_USER_PREFS_TYPE_NAME, DINGOS_SAVED_SEARCHES_TYPE_NAME, DINGOS_DEFAULT_SAVED_SEARCHES

from braces.views import LoginRequiredMixin
from view_classes import BasicFilterView, BasicDetailView, BasicTemplateView


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
        'identifier').select_related().distinct().order_by('-latest_of__pk')

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

class InfoObjectsEmbedded(BasicFilterView):
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


    filterset_class = FactTermValueFilter

    queryset =  InfoObject2Fact.objects.all().\
        exclude(iobject__latest_of=None). \
        exclude(iobject__iobject_family__name__exact=DINGOS_INTERNAL_IOBJECT_FAMILY_NAME). \
        prefetch_related('iobject',
            'iobject__iobject_type',
            'fact__fact_term',
            'fact__fact_values').select_related().distinct().order_by('iobject__id')

class InfoObjectView_wo_login(BasicDetailView):
    """
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
        # as a hack, we clear here the settings in the session. This will
        # lead to a reload of the user config into the session data
        try:
            del(self.request.session['customization'])
            del(self.request.session['customization_for_authenticated'])
        except KeyError, err:
                pass
        context = super(InfoObjectView_wo_login, self).get_context_data(**kwargs)

        context['show_NodeID'] = self.request.GET.get('show_nodeid',False)
        context['iobject2facts'] = self.iobject2facts
        try:
            context['highlight'] = self.request.GET['highlight']
        except KeyError:
            context['highlight'] = None

        return context


class InfoObjectView(LoginRequiredMixin,InfoObjectView_wo_login):
    pass

class UserPrefsView(InfoObjectView_wo_login):
    def get_object(self):
        return UserData.get_user_data_iobject(user=self.request.user,data_kind=DINGOS_USER_PREFS_TYPE_NAME)

class CustomSearchesEditView(BasicTemplateView):
    template_name = 'dingos/%s/edits/SavedSearchesEdit.html' % DINGOS_TEMPLATE_FAMILY
    title = 'Saved searches'

    form_class = formset_factory(EditSavedSearchesForm, can_order=True, can_delete=True)

    formset = None


    def get_context_data(self, **kwargs):
        context = super(CustomSearchesEditView, self).get_context_data(**kwargs)

        # delete the saved search within session to avoid pollution of session store
        # and add the temporary search to context
        if self.request.session.get('new_search'):
           context['new_search'] = self.request.session['new_search']
           del self.request.session['new_search']
           self.request.session.modified = True

           # set form id for proper formset handling
           # ...it's ugly but Django needs proper formed HTML fields
           nid = len(self.request.session['saved_searches']['dingos'])
           context['new_search'].update( { 'id' : nid, 'order' : nid + 1 } )


        context['formset'] = self.formset

        return context

    def get(self, request, *args, **kwargs):
        user_data = self.get_user_data()
        saved_searches = user_data['saved_searches'].get('dingos',[])
        print saved_searches
        initial = []

        for saved_search in saved_searches:
            initial.append({'title': saved_search['title'],
                            'view' : saved_search['view'],
                            'parameter' : saved_search['parameter']})
        if self.request.session.get('new_search'):
            initial.append({'title': "",
                            'view' : self.request.session['new_search']['view'],
                            'parameter' : self.request.session['new_search']['parameter']})

        self.formset = self.form_class(initial=saved_searches)


        return super(BasicTemplateView,self).get(request, *args, **kwargs)

    def count_forms(self, post):
        """
        Returns the number of searches in a given request.POST dict
        """

        forms = []
        regex = re.compile(r'^form-(?P<id>\d)-(paramater|path|title)$')
        for k, v in post.iteritems():
            m = re.match(regex, k)
            if m:
                d = m.groupdict()
                if not d['id'] in forms:
                    forms.append(d['id'])

        return len(forms)


    def post(self, request, *args, **kwargs):
        data = { u'form-TOTAL_FORMS' : u'%s' % self.count_forms(request.POST.dict()),
                 u'form-INITIAL_FORMS' : u'0',
                 u'form-MAX_NUM_FORMS' : u'',
                 u'form-MIN_NUM_FORMS' : u'',
               }
        data.update(request.POST.dict())
        form_class = formset_factory(EditSavedSearchesForm, can_order=True)
        formset = form_class(data)

        if formset.is_valid() and request.user.is_authenticated():
            saved_searches = { 'dingos' : [] }
            for form in formset.ordered_forms:
                search = form.cleaned_data
                saved_searches['dingos'].append( { 'view' : search['view'], 
                                                   'parameter' : search['parameter'],
                                                   'title' : search['title'],
                                                   'priority' : '%s' % search['ORDER'],
                                                 }
                                               )
            UserData.store_user_data(user=request.user,
                                     data_kind=DINGOS_SAVED_SEARCHES_TYPE_NAME,
                                     user_data=saved_searches,
                                     iobject_name = "Saved searches of user '%s'" % request.user.username)

            # enforce reload of session
            del request.session['customization']
            request.session.modified = True

        else:
            print "NOT valid! --> ", formset.errors 

        return super(BasicTemplateView,self).get(request, *args, **kwargs)

class InfoObjectJSONView(BasicDetailView):
    # Config for Prefetch/SelectRelated Mixins_
    select_related = ()
    prefetch_related = () # The to_dict function itself defines the necessary prefetch_stuff

    model = InfoObject

    def render_to_response(self, context):
        #return self.get_json_response(json.dumps(context['object'].show_elements(""),indent=2))
        include_node_id = self.request.GET.get('include_node_id',False)

        return self.get_json_response(json.dumps(context['object'].to_dict(include_node_id=include_node_id),indent=2))

    def get_json_response(self, content, **httpresponse_kwargs):
        return http.HttpResponse(content,
                                 content_type='application/json',
                                 **httpresponse_kwargs)

