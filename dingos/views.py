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

from django import http


from django.db.models import F

from dingos.models import Identifier, InfoObject2Fact, InfoObject
from dingos.filter import InfoObjectFilter, FactTermValueFilter, IdSearchFilter

from dingos import DINGOS_TEMPLATE_FAMILY

from view_classes import BasicFilterView, BasicDetailView, BasicTemplateView



class InfoObjectList(BasicFilterView):

    template_name = 'dingos/%s/lists/InfoObjectList.html' % DINGOS_TEMPLATE_FAMILY

    breadcrumbs = (('Dingo',None),
                   ('List',None),
                   ('InfoObject',None))

    paginate_by = 15

    filterset_class= InfoObjectFilter

    title = 'List of Info Objects (generic filter)'

    queryset = InfoObject.objects.exclude(latest_of=None).prefetch_related(
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

    paginate_by = 15

    filterset_class= IdSearchFilter

    title = 'ID-based filtering'

    queryset = InfoObject.objects.exclude(latest_of=None).prefetch_related(
        'iobject_type',
        'iobject_family',
        'iobject_family_revision',
        'identifier').select_related().distinct().order_by('-latest_of__pk')

class InfoObjectsEmbedded(BasicFilterView):
    template_name = 'dingos/%s/lists/InfoObjectEmbedded.html' % DINGOS_TEMPLATE_FAMILY

    breadcrumbs = (('Dingo',None),
                   ('List',None),
                   ('InfoObject',None))

    paginate_by = 15

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

    paginate_by = 15

    title = 'Fact-based filtering'


    filterset_class = FactTermValueFilter

    queryset =  InfoObject2Fact.objects.all().exclude(iobject__latest_of=None).prefetch_related('iobject',
                                                                                                'iobject__iobject_type',
                                                                                                'fact__fact_term',
                                                                                                'fact__fact_values').select_related().distinct().order_by('iobject__id')



class InfoObjectView(BasicDetailView):
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

    max_embedded = 5

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


    max_embedded = 5

    template_name = 'dingos/%s/details/InfoObjectDetails.html' % DINGOS_TEMPLATE_FAMILY

    title = 'Info Object Details'

    def get_context_data(self, **kwargs):
        context = super(InfoObjectView, self).get_context_data(**kwargs)
        context['max_embedded'] = self.max_embedded

        context['show_NodeID'] = self.request.GET.get('show_nodeid',False)
        context['iobject2facts'] = self.iobject2facts
        try:
            context['highlight'] = self.request.GET['highlight']
        except KeyError:
            context['highlight'] = None

        return context




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

