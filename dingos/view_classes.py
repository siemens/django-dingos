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

import csv, collections, copy, json, StringIO, importlib
from queryparser.queryparser import QueryParser
from queryparser.placeholder_parser import PlaceholderParser

import re
from datetime import date, timedelta
import datetime

from django import forms, http
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core import urlresolvers
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.paginator import PageNotAnInteger, Paginator, EmptyPage
from django.http import HttpResponseRedirect, HttpResponse
from django.utils.http import urlquote_plus
from django.views.generic import DetailView, ListView, TemplateView, View
from django.views.generic.base import ContextMixin
from django_filters.views import FilterView
from django.http import Http404
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from braces.views import LoginRequiredMixin, SelectRelatedMixin,PrefetchRelatedMixin

from dingos import DINGOS_TEMPLATE_FAMILY, \
                   DINGOS_USER_PREFS_TYPE_NAME, \
                   DINGOS_DEFAULT_USER_PREFS, \
                   DINGOS_SAVED_SEARCHES_TYPE_NAME, \
                   DINGOS_DEFAULT_SAVED_SEARCHES,\
                   DINGOS_SEARCH_POSTPROCESSOR_REGISTRY,\
                   DINGOS_SEARCH_EXPORT_MAX_OBJECTS_PROCESSING,\
                   TAGGING_REGEX

from dingos import graph_traversal
from dingos.core.template_helpers import ConfigDictWrapper
from dingos.core.utilities import get_dict, replace_by_list, listify
from dingos.forms import CustomQueryForm, BasicListActionForm, SimpleMarkingAdditionForm, PlaceholderForm, TaggingAdditionForm
from dingos.queryparser.placeholder_parser import PlaceholderParser
from dingos.models import InfoObject, UserData, Marking2X, Fact, dingos_class_map, TaggingHistory, Identifier, vIO2FValue

from core.http_helpers import get_query_string
from taggit.models import Tag
from django.apps import apps

POSTPROCESSOR_REGISTRY = {}


for (postprocessor_key,postprocessor_data) in DINGOS_SEARCH_POSTPROCESSOR_REGISTRY.items():
    if 'module' in postprocessor_data:
        try:
            my_module = importlib.import_module(postprocessor_data['module'])
        except:
            my_module = None
        if my_module:
            POSTPROCESSOR_REGISTRY[postprocessor_key] = [getattr(my_module,postprocessor_data['class'])]
    elif 'postprocessor_predicate' in postprocessor_data:
        predicate = postprocessor_data['postprocessor_predicate']
        postprocessor_list = []
        for (postprocessor_key2,postprocessor_data2) in DINGOS_SEARCH_POSTPROCESSOR_REGISTRY.items():
            print predicate(postprocessor_key2,postprocessor_data2)
            print postprocessor_key2
            print postprocessor_data2
            if predicate(postprocessor_key2,postprocessor_data2) and 'module' in postprocessor_data2:
                try:
                    my_module = importlib.import_module(postprocessor_data2['module'])
                except:
                    my_module = None
                if my_module:
                    postprocessor_list.append(getattr(my_module,postprocessor_data2['class']))
        POSTPROCESSOR_REGISTRY[postprocessor_key] = postprocessor_list

print "Registry %s" % POSTPROCESSOR_REGISTRY


class UncountingPaginator(Paginator):
    """
    Counting the number of existing data records can be incredibly slow
    in postgresql. For list/filter views where we find no solution for
    this problem, we disable the counting. For this, we need a modified
    paginator that always returns a huge pagecount.

    """

    def validate_number(self, number):
        """
        Validates the given 1-based page number.
        """
        try:
            number = int(number)
        except (TypeError, ValueError):
            raise PageNotAnInteger('That page number is not an integer')
        if number < 1:
            raise EmptyPage('That page number is less than 1')
        if number > self.num_pages:
            # The original paginator raises an exception here if
            # the required page does not contain results. This
            # we need to disable, of course
            pass

        return number

    def page(self, number):
        """
        Returns a Page object for the given 1-based page number.
        """
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page
        # The original Paginator makes the test shown above;
        # we disable this test. This does not cause problems:
        # a queryset handles a too large upper bound gracefully.
        #if top + self.orphans >= self.count:
        #    top = self.count
        return self._get_page(self.object_list[bottom:top], number, self)

    count = 10000000000

    num_pages = 10000000000

    # Page-range: returns a 1-based range of pages for iterating through within
    # a template for loop. For our modified paginator, we return an empty set.
    # This is likely to lead to problems where the page_range is used. In our
    # views, this is not the case, it seems.

    page_range = []


class CommonContextMixin(ContextMixin):
    """
    Each view passes a 'context' to the template with which the view
    is rendered. By including this mixin in a class-based view, the
    context is enriched with the contents expected by all Dingos
    templates.
    """

    object_list_len = None

    tags_dict = None

    def get_context_data(self, **kwargs):

        context = super(CommonContextMixin, self).get_context_data(**kwargs)

        context['title'] = self.title if hasattr(self, 'title') else '[TITLE MISSING]'

        context['list_actions'] = self.list_actions if hasattr(self, 'list_actions') else []

        if 'object_list' in context and self.object_list_len == None:
            self.object_list_len = len(list(context['object_list']))
        context['object_list_len'] = self.object_list_len


        user_data_dict = self.get_user_data()

        # We use the ConfigDictWrapper to wrap the data dictionaries. This allows the
        # following usage within a template, e.g., for ``customizations``::
        #
        #      customizations.<defaut_value>.<path_to_value_in_dict separated by '.'s>
        #
        # For example:
        #
        #      customizations.5.dingos.widget.embedding_objects.lines
        #
        # where 5 is the default value that will be taken if the dictionary lookup
        # ``customizations['dingos']['widget']['embedding_objects']['lines']`` does
        # not yield a different value.

        settings = self.request.session.get('customization')

        wrapped_settings = ConfigDictWrapper(config_dict=user_data_dict.get('customization',{}))
        wrapped_saved_searches = ConfigDictWrapper(config_dict=user_data_dict.get('saved_searches',{}))

        settings = self.request.session.get('customization')

        context['customization'] = wrapped_settings
        context['saved_searches'] = wrapped_saved_searches

        return context


class ViewMethodMixin(object):
    """
    We use this Mixin to enrich view with methods that are required
    by certain templates and template tags. In order to use
    these template tags from a given view, simply add this
    mixin to the parent classes of the view.
    """
    def get_query_string(self,*args,**kwargs):
        """
        Allows access to query string (with facilities to manipulate the string,
        e.g., removing or adding query attributes. We use this, for example,
        in the paginator, which needs to create a link with the current
        query and change around the 'page' part of the query string.
        """
        return get_query_string(self.request,*args,**kwargs)

    def get_user_data(self,load_new_settings=False):
        """
        Extracts user data, either from user session or from
        database (for each User, an InfoObject is used to
        store data of a certain kind (e.g., user customization,
        saved searches, etc.). If for a given user,
        no InfoObject exists for a given type of user-specific data,
        the default data is read from the settings and
        an InfoObject with default settings is created.

        The function returns a dictionary of form

        {'customization': <dict with user customization>,
         'saved_searches': <dict with saved searches>
         }


        """

        # Below, we retrieve user-specific data (user preferences, saved searches, etc.)
        # We take this data from the session -- if it has already been
        # loaded in the session. If not, then we load the data into the session first.
        #
        # Things are a bit tricky, because users can first be unauthenticated,
        # then log in, then log off again. This must be reflected in the user data
        # that is loaded into the session.
        #
        # There are four cases if settings exist within session scope:
        # 1.) unauthenticated user && non-anonymous settings exist in session --> load
        # 2.) unauthenticated user && anonymous settings --> pass
        # 3.) authenticated user && non-anonymous settings --> pass
        # 4.) authenticated user && anonymous settings --> load

        settings = self.request.session.get('customization')

        saved_searches = self.request.session.get('saved_searches')

        if settings and not load_new_settings:

            # case 1.)
            if (not self.request.user.is_authenticated()) \
                and self.request.session.get('customization_for_authenticated'):
                load_new_settings = True

            # case 4.)
            elif self.request.user.is_authenticated() \
                and not self.request.session.get('customization_for_authenticated'):
                load_new_settings = True

        else:
            load_new_settings = True

        if load_new_settings:
            # Load user settings. If for the current user, no user settings have been
            # stored, retrieve the default settings and store them (for authenticated users)

            if self.request.user.is_authenticated():
                user_name = self.request.user.username
            else:
                user_name = "unauthenticated user"

            self.request.session['customization_for_authenticated']=self.request.user.is_authenticated()



            settings = UserData.get_user_data(user=self.request.user,data_kind=DINGOS_USER_PREFS_TYPE_NAME)

            if not settings:
                UserData.store_user_data(user=self.request.user,
                                         data_kind=DINGOS_USER_PREFS_TYPE_NAME,
                                         user_data=DINGOS_DEFAULT_USER_PREFS,
                                         iobject_name= "User preferences of user '%s'" % user_name)

                settings = UserData.get_user_data(user=self.request.user,data_kind=DINGOS_USER_PREFS_TYPE_NAME)



            # Do the same for saved searches

            saved_searches = UserData.get_user_data(user=self.request.user, data_kind=DINGOS_SAVED_SEARCHES_TYPE_NAME)
            if not saved_searches:

                UserData.store_user_data(user=self.request.user,
                                         data_kind=DINGOS_SAVED_SEARCHES_TYPE_NAME,
                                         user_data=DINGOS_DEFAULT_SAVED_SEARCHES,
                                         iobject_name = "Saved searches of user '%s'" % user_name)
                saved_searches = UserData.get_user_data(user=self.request.user, data_kind=DINGOS_SAVED_SEARCHES_TYPE_NAME)

            self.request.session['customization'] = settings
            self.request.session['saved_searches'] = saved_searches

        return {'customization': settings,
                'saved_searches' : saved_searches}


    def _lookup_user_data(self,*args,**kwargs):
        """
        Generic function for looking up values in
        a user-specific dictionary. Use as follows::

           _lookup_user_data('path','to','desired','value','in','dictionary',
                             default = <default value>,
                             data_kind = 'customization'/'saved_searches')

        """
        user_data = self.get_user_data()
        data_kind = kwargs.get('data_kind','customization')
        try:
            del(kwargs['data_kind'])
        except KeyError, err:
            pass
        default_value = kwargs['default']

        result =  get_dict(user_data,data_kind,*args,**kwargs)
        try:
            result = int(result)
        except:
            pass

        if not isinstance(result,default_value.__class__):
            return default_value
        else:
            return result

    def lookup_customization(self,*args,**kwargs):
        """
        Lookup value in user-customization dictionary. Use as follows::

             lookup_customization('path','to','desired','value','in','dictionary',
                                 default = <default value>)
        """
        kwargs['data_kind']='customization'
        return self._lookup_user_data(*args,**kwargs)

    def lookup_saved_searches(self,*args,**kwargs):
        """
        Lookup value in saved_searches dictionary. Use as follows::

             lookup_customization('path','to','desired','value','in','dictionary',
                                 default = <default value>)
        """

        kwargs['data_kind']='saved_searches'
        return self._lookup_user_data(*args,**kwargs)

    def obj_by_pk(self,pk):
        """
        This is a hack for accessing objects from a template by pk.
        """
        for o in self.object_list:
            if "%s" % o.pk == "%s" % pk:
                return o
        return None


class BasicListView(CommonContextMixin,ViewMethodMixin,LoginRequiredMixin,ListView):
    """
    Basic class for defining list views: includes the necessary mixins
    and code to read pagination information from user customization.
    """

    template_name = 'dingos/%s/lists/base_lists_two_column.html' % DINGOS_TEMPLATE_FAMILY

    breadcrumbs = ()

    counting_paginator = False

    @property
    def paginator_class(self):
        if not self.counting_paginator:
            return UncountingPaginator
        else:
            return super(BasicListView,self).paginator_class

    @property
    def paginate_by(self):
        item_count = self.lookup_customization('dingos','view','pagination','lines',default=20)
        return item_count


class BasicFilterView(CommonContextMixin,ViewMethodMixin,LoginRequiredMixin,FilterView):
    """
    Basic class for defining filter views: includes the necessary mixins
    and code to

    - return results in JSON format for api calls to the search
    - read pagination information from user customization.
    - save filter settings as saved search

    Have a look at the views derived from this view class in views.py to
    get a feeling for how the class is to be used.

    """

    template_name = 'dingos/%s/lists/base_lists_two_column.html' % DINGOS_TEMPLATE_FAMILY

    breadcrumbs = ()

    counting_paginator = False

    graph = None

    fields_for_api_call = ['name']

    list_actions = [

                ('Mark', 'url.dingos.action.add_marking', 0),
                ('Tag', 'url.dingos.action.add_tagging', 0)

            ]

    @property
    def paginator_class(self):
        if not self.counting_paginator:
            return UncountingPaginator
        else:
            return super(BasicFilterView,self).paginator_class

    @property
    def paginate_by(self):
        return self.lookup_customization('dingos','view','pagination','lines',default=20)

    def get(self, request, *args, **kwargs):
        if request.GET.get('api_call'):
            # The filter view is called via the API. Therefore, we
            # - carry out the query by populating the context
            # - write the result into the view such that it can be
            #   extracted by the mantis_api module (the module
            #   instantiates the view and then accesses it to
            #   retrieve the results)

            filterset_class = self.get_filterset_class()
            self.filterset = self.get_filterset(filterset_class)
            self.object_list = self.filterset.qs
            context = self.get_context_data(filter=self.filterset,
                                        object_list=self.object_list)

            # Default postprocessor is JSON
            postprocessor_class = POSTPROCESSOR_REGISTRY['json']

            # We need to find out the query mode; a filter view has
            # either the 'model' or the 'filterset_class' set; we
            # extract the query mode from whatever attribute is present.

            try:
                query_mode = self.model.__name__
            except:
                query_mode = self.filterset_class.Meta.model.__name__


            postprocessor = postprocessor_class(query_mode=self.filterset_class.Meta.model.__name__,
                                                format='dict')

            if postprocessor.query_mode == 'InfoObject':
                # TODO: this looks fishy... make sure that all __init__ stuff is carried out
                # in some other way.
                postprocessor.object_list = context['object_list']
                postprocessor.initialize_object_details()
            else:
                postprocessor.io2fs = context['object_list']


            (content_type,result) = postprocessor.export(*self.fields_for_api_call)

            # Write the results into the view
            self.api_result = result
            self.api_result_content_type = content_type

            # This view can be called in 'api_call'-mode by putting an 'api_call' parameter
            # into the URL. If that is the case, we return a page that shows the result
            # in JSON format.
            #
            # What we do here is really irrelevant for the call via the API: the API
            # instantiates the view but does not care about what the view returns!
            #
            self.template_name = 'dingos/%s/searches/API_Search_Result.html' % DINGOS_TEMPLATE_FAMILY
            return super(BasicFilterView, self).get(request, *args, **kwargs)

        # If this was not an API call, we see whether the filter form was submitted
        elif request.GET.get('action','Submit Query') == 'Submit Query':
            return super(BasicFilterView,self).get(request, *args, **kwargs)
        else:
            # Otherwise, the form was submitted with pressing the 'save search' button. In this case,
            # we write the parameters into the session such that they can be retrieved by the
            # save-search-view and then redirect to that view.

            match = urlresolvers.resolve(request.path_info)

            # write data into session
            request.session['new_search'] = {
                # do the whole magic within a single line (strip empty elements + action, urlencode, creating GET string
                "parameter" : "&".join(list( "%s=%s" % (k,v) for k, v in request.GET.iteritems() if v and k != "action")),
                "view" : match.url_name,
            }

            # Redirect to edit view as this takes care of the rest
            return HttpResponseRedirect(urlresolvers.reverse('url.dingos.admin.edit.savedsearches'))


class BasicDetailView(CommonContextMixin,
                      ViewMethodMixin,
                      SelectRelatedMixin,
                      PrefetchRelatedMixin,
                      DetailView):

    select_related = ()
    prefetch_related = ()

    breadcrumbs = (('Dingo',None),
                   ('View',None),
    )

    @property
    def paginate_by(self):
        return self.lookup_customization('dingos','view','pagination','lines',default=20)


class BasicTemplateView(CommonContextMixin,
                       ViewMethodMixin,
                       LoginRequiredMixin,
                       TemplateView):

    breadcrumbs = (('Dingo',None),
                   ('View',None),
    )


class BasicCustomQueryView(BasicListView):
    page_to_show = 1

    counting_paginator = False

    template_name = 'dingos/%s/searches/CustomInfoObjectSearch.html' % DINGOS_TEMPLATE_FAMILY

    title = 'Custom Info Object Search'

    form = None
    placeholder_form = None
    format = None
    distinct = True

    query_base = InfoObject.objects.exclude(latest_of=None)

    prefetch_related = ('iobject_type',
                        'iobject_type__iobject_family',
                        'iobject_family',
                        'identifier__namespace',
                        'iobject_family_revision',
                        'identifier')

    paginate_by_value = 5

    col_headers = ["Identifier", "Object Timestamp", "Import Timestamp", "Name", "Object Type", "Family"]
    selected_cols = ["identifier", "timestamp", "create_timestamp", "name", "iobject_type.name", "iobject_family.name"]

    @property
    def paginate_by(self):
        return self.paginate_by_value

    def get_context_data(self, **kwargs):
        """
        Call 'get_context_data' from super and include the query form in the context
        for the template to read and display.
        """

        context = super(BasicCustomQueryView, self).get_context_data(**kwargs)
        context['form'] = self.form
        context['placeholder_form'] = self.placeholder_form
        context['col_headers'] = self.col_headers
        context['selected_cols'] = self.selected_cols
        context['query']= self.request.GET.get('query','')
        if self.request.GET.get('nondistinct',False):
            context['distinct'] = False
        else:
            context['distinct'] = True
        return context

    def get(self, request, *args, **kwargs):

        self.form = CustomQueryForm(request.GET)
        self.queryset = []
        if self.request.GET.get('nondistinct',False):
            distinct = False
        else:
            distinct = self.distinct

        if request.GET.get('action','Submit Query') == 'Save Search':
            match = urlresolvers.resolve(request.path_info)

            # write data into session
            request.session['new_search'] = {
                # do the whole magic within a single line (strip empty elements + action, urlencode, creating GET string
                "parameter" : "&".join(list( "%s=%s" % (urlquote_plus(k),urlquote_plus(v))
                                              for k, v in request.GET.iteritems() if v and k not in  ["action",
                                                                                                      "csrfmiddlewaretoken",
                                                                                                      "query"])),
                "view" : match.url_name,
                "custom_query" : request.GET.get('query','')
                }

            # Redirect to edit view as this takes care of the rest
            return HttpResponseRedirect(urlresolvers.reverse('url.dingos.admin.edit.savedsearches'))

        if self.form.is_valid(): # 'execute_query' in request.GET and self.form.is_valid():


            if request.GET.get('query', '') == "":
                messages.error(self.request, "Please enter a query.")
            else:
                try:
                    query = self.form.cleaned_data['query']

                    if "{{" in query and "}}" in query:
                        placeholders = []
                        parser = PlaceholderParser()
                        for raw in re.findall("\{\{[^\}]+\}\}", query):
                            # Cut {{ and }}
                            placeholder = parser.parse(raw[2:-2])
                            placeholders.append({"raw": raw, "parsed": placeholder})
                        self.placeholder_form = PlaceholderForm(request.GET, placeholders=placeholders)

                        for one in placeholders:
                            placeholder = one["parsed"]

                            if placeholder["field_name"] in request.GET:
                                field_value = request.GET[placeholder["field_name"]]
                                if "interpret_as" in placeholder.keys() and placeholder["interpret_as"] == "date":
                                    field_value = field_value.strip()
                                    if field_value.startswith("today"):
                                        the_date = date.today()
                                        if re.match("today( )*(\-|\+)( )*\d+", field_value):
                                            delta_days = field_value.split("today")[1].strip()
                                            the_date = the_date - timedelta(days=int(delta_days)*(-1))
                                        field_value = the_date.strftime("%Y-%m-%d")
                                query = query.replace(one["raw"], "\"%s\"" % field_value)
                            else:
                                query = query.replace(one["raw"], "\"%s\"" % placeholder["default"])




                    parser = QueryParser()
                    self.paginate_by_value = int(self.form.cleaned_data['paginate_by'])
                    if self.form.cleaned_data['page']:
                        self.page_to_show = int(self.form.cleaned_data['page'])

                    # Generate and execute queries

                    filter_collections = parser.parse(str(query))
                    
                    # TODO: the code that does the processing of the query should not be here
                    # but part of the filter_collections object. This is because the query may
                    # also be used at other places (e.g. below in the MarkingsAction view
                    # If the user defined a referenced_by-preprocessing

                    objects = self.query_base.all()

                    if filter_collections.refby_filter_collection:
                        # Preprocessing for referenced-by query
                        refby_filter_collection = filter_collections.refby_filter_collection.filter_collection
                        objects = refby_filter_collection.build_query(base=objects)
                        objects = objects.distinct()
                        # Retrieve pk list out of the object list
                        pks = [one.pk for one in objects]
                        pks = graph_traversal.follow_references(pks, **filter_collections.refby_filter_args)

                        # Filter objects
                        objects = self.query_base.all().filter(pk__in=pks)


                    # Processing for main query
                    formatted_filter_collection = filter_collections.formatted_filter_collection

                    if hasattr(formatted_filter_collection, 'filter_collection'):
                        objects = formatted_filter_collection.filter_collection.build_query(base=objects)

                    if distinct:
                        if isinstance(distinct, tuple):
                            objects = objects.order_by(*list(self.distinct)).distinct(*list(self.distinct))
                        elif isinstance(distinct,bool):
                            if distinct:
                                objects = objects.distinct()
                        else:
                            raise TypeError("'distinct' must either be True or a tuple of field names.")

                    # Output format
                    result_format = formatted_filter_collection.format

                    # Filter selected columns for export
                    formatting_arguments = formatted_filter_collection.build_format_arguments(query_mode=self.query_base.model.__name__)

                    col_specs = formatting_arguments['columns']
                    misc_args = formatting_arguments['kwargs']
                    prefetch = formatting_arguments['prefetch_related']


                    if col_specs['headers']:
                        self.col_headers = col_specs['headers']
                        self.selected_cols = col_specs['selected_fields']

                        if prefetch:
                            objects = objects.prefetch_related(*prefetch)
                    else:
                        if isinstance(self.prefetch_related, tuple):
                            objects = objects.prefetch_related(*list(self.prefetch_related))
                        else:
                            raise TypeError("'prefetch_related' must either be True or a tuple of field names.")

                    self.queryset = objects


                    if request.GET.get('api_call') and result_format == 'default':
                        result_format = 'csv'


                    if result_format == 'default':
                        return super(BasicListView, self).get(request, *args, **kwargs)

                    request.GET.get('api_call')

                    postprocessor = formatting_arguments['postprocessor']

                    if request.GET.get('api_call') and not postprocessor:
                        postprocessor_class = POSTPROCESSOR_REGISTRY['json']
                        postprocessor = postprocessor_class(query_mode=self.query_base.model.__name__)

                    if postprocessor:

                        if postprocessor.exporter_name in ['csv','json','table']:
                            pagination = self.paginate_by_value
                        else:
                            pagination = DINGOS_SEARCH_EXPORT_MAX_OBJECTS_PROCESSING

                        p = self.paginator_class(self.queryset, pagination)
                        response = HttpResponse(content_type='text') # '/csv')

                        if postprocessor.query_mode == 'InfoObject':
                            # TODO: this looks fishy... make sure that all __init__ stuff is carried out
                            # in some other way.
                            postprocessor.object_list = p.page(self.page_to_show).object_list
                            postprocessor.initialize_object_details()
                        else:
                            postprocessor.io2fs = p.page(self.page_to_show).object_list

                        if request.GET.get('api_call') or result_format=='table':
                            postprocessor.format = 'dict'
                        (content_type,result) = postprocessor.export(*col_specs['selected_fields'],
                                                                     **misc_args)


                        if result_format == 'table':
                            self.results = result
                            print result
                            self.col_headers = col_specs['headers']
                            self.selected_cols = col_specs['selected_fields']
                            self.template_name = 'dingos/%s/searches/CustomSearch.html' % DINGOS_TEMPLATE_FAMILY
                            return super(BasicListView, self).get(request, *args, **kwargs)

                        if request.GET.get('api_call'):
                            self.api_result = result
                            self.api_result_content_type = content_type
                            self.template_name = 'dingos/%s/searches/API_Search_Result.html' % DINGOS_TEMPLATE_FAMILY
                            return super(BasicCustomQueryView, self).get(request, *args, **kwargs)
                        else:
                            response = HttpResponse(content_type=content_type) # '/csv')
                            response.write(result)
                            return response
                    else:
                        raise ValueError('Unsupported output format')
                except Exception as ex:
                    self.queryset = InfoObject.objects.filter(pk=-1)
                    messages.error(self.request, str(ex))

        return super(BasicListView, self).get(request, *args, **kwargs)


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        else:
            return super(DateTimeEncoder, self).default(obj)


class BasicJSONView(CommonContextMixin,
                    ViewMethodMixin,
                    LoginRequiredMixin,
                    TemplateView):

    indent = 2

    @property
    def returned_obj(self):
        return {"This":"That"}

    request = None

    def get(self, request, *args, **kwargs):
        self.request= request
        context = self.get_context_data(**kwargs)
        if request.GET.get('test_call'):
            self.api_result = self.returned_obj
            self.api_result_content_type = "json"
            self.template_name = 'dingos/%s/searches/API_Search_Result.html' % DINGOS_TEMPLATE_FAMILY
            return super(BasicJSONView, self).get(request, *args, **kwargs)
        else:
            return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


    def render_to_response(self, context):
        if self.request.GET.get('test_call'):
            return super(BasicJSONView, self).render_to_response(context)
        returned_obj = self.returned_obj
        if isinstance(returned_obj,basestring):
            json_string = returned_obj
        else:
            json_string = json.dumps(returned_obj,indent=self.indent,cls=DateTimeEncoder)

        return self._get_json_response(json_string)

    def _get_json_response(self, content, **httpresponse_kwargs):
         return http.HttpResponse(content,
                                  content_type='application/json',
                                  **httpresponse_kwargs)


class BasicXMLView(CommonContextMixin,
                    ViewMethodMixin,
                    LoginRequiredMixin,
                    TemplateView):

    @property
    def returned_xml(self):
        return ""


    def render_to_response(self, context):
        xml = self.returned_xml
        if not xml:
            raise Http404
        else:
            return http.HttpResponse(xml,
                                     content_type='application/xml')


class BasicView(CommonContextMixin,
                ViewMethodMixin,
                LoginRequiredMixin,
                View):

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def render_to_response(self, context):
        raise NotImplementedError("No render_to_response method implemented!")


class BasicListActionView(BasicListView):

    # Override the following parameters in views inheriting from this view.

    title = 'Carry out actions on model instances'

    description = """Provide here a brief description for the user of what to do -- this will be displayed
                     in the view."""

    template_name = 'dingos/%s/actions/base_action_on_selected_list.html' % DINGOS_TEMPLATE_FAMILY


    # The query below will be used by the view to retrieve the model instances to be acted upon
    # from the database.
    #
    # IMPORTANT: You must provide a query that restricts the model instances to those instances
    # that the user in question really allowed to act upon -- otherwise, a malicious user may
    # fiddle with the POST request and insert primary keys of instances he should not have access to.
    #
    # In order to implement such a restriction, you will almost certainly have to use hte ``@property``
    # mechanism of Python when specifying the query, because you will need to access the view  via
    # ``self`` (e.g. to extract the user via ``self.request.user`` ::
    #
    #         @property:
    #         def action_model_query(self):
    #             query = <build your query>
    #             return query
    #

    action_model_query = InfoObject.objects.all()

    form_class = BasicListActionForm

    preprocess_action_objects = None


    # kwargs dict to be passed to form for initialization;
    # Use this to dynamically adapt a more form to this particular view
    # by modifying the form according to the arguments passed to its
    # __init__ function.

    form_init_dict = {}

    # Action List

    # Elements of the list should have the following form:
    # {'action_predicate': <function taking form_data and object to be acted upon,
    #                       returning True or False
    #                       whether action is to be carried out on the given object>,
    #  'action_function': <function taking cleaned form data  and object to be acted upon
    #                      Should return
    #                         (True, 'Success message')
    #                      for successful execution or
    #                         (False, 'Error message')
    #                      for problem in executing action
    #
    # For each marking to be added, the list is traversed; the first action for which the
    # predicate returned True is carried out.


    action_list = []


    # If no action could be found (and 'apply_marking_wo_action' is set to False)
    # we return the following error message. Use this to provide the user with more
    # information about why you think that no actions could be found.

    no_action_error_message = "No valid action could be found for the object."


    # If True, action is not actually carried out
    debug_action = False


    ### Class code below

    # We do not paginate: there should be no need, because all objects that are displayed
    # have been selected by the user via a checkbox, which limits the numbers.
    # Also, with the current implementation of the Template, which iterates through the
    # checkboxes in the form rather than the object list, pagination by simply inheriting
    # from the basic list view template dos not work.

    paginate_by = False
    form = None


    # The queryset (required for the BasicListView) will be filled in the post-method
    # below, but we need to declare it here.

    queryset = None

    def _set_initial_form(self,*args,**kwargs):
        action_objects = self.request.POST.getlist('action_objects')
        if self.preprocess_action_objects:
            action_objects = self.preprocess_action_objects(action_objects)
        self.queryset = self.action_model_query.filter(id__in=action_objects)
        kwargs['choices'] = action_objects
        initial = {
            'checked_objects' : action_objects,
            'checked_objects_choices' : ','.join(action_objects)
        }
        self.form = self.form_class(initial=initial,*args,**kwargs)

    def _set_post_form(self,*args,**kwargs):
        choices =  self.request.POST.dict().get('checked_objects_choices').split(',')
        self.queryset = self.action_model_query.filter(id__in=choices)
        kwargs['choices'] = choices
        self.form = self.form_class(self.request.POST,*args,**kwargs)

    def post(self, request, *args, **kwargs):

        # If this is the first time, the view is rendered, it has been
        # called as action from another view; in that case, there must be
        # the result of the multiple-choice field with which objects
        # to perform the action on were selected in the POST request.
        # So we use the presence of 'action_objects' to see whether
        # this is indeed the first call.

        if 'action_objects' in self.request.POST:

            self._set_initial_form()
            return super(BasicListActionView,self).get(request, *args, **kwargs)
        else:
            # So the view has been called a second time by submitting the form in the view
            # rather than from a different view. So we need to process the data in the form


            self._set_post_form(request.POST,
                                **self.form_init_dict)

            # React on a valid form
            if self.form.is_valid():
                form_data = self.form.cleaned_data
                for obj_pk in form_data['checked_objects']:

                    obj_to_be_acted_upon = self.action_model_query.get(pk=obj_pk)
                    action_list = self.action_list

                    found_action = False
                    for action  in action_list:
                        if found_action:
                            break
                        action_predicate = action['action_predicate']
                        action_function = action['action_function']

                        if action_predicate(form_data,obj_to_be_acted_upon):
                            found_action = True

                            if self.debug_action:
                                (success,action_msg) = (True,"DEBUG: Action has not been carried out")
                            else:
                                (success,action_msg) = action_function(form_data,obj_to_be_acted_upon)
                            if success:
                                messages.success(self.request, action_msg)
                            else:
                                messages.error(self.request, action_msg)

                    if not found_action:
                        messages.error(self.request,self.no_action_error_message)


                form_data['checked_objects'] = []
                self._set_post_form(form_data,**self.form_init_dict)
                return super(BasicListActionView,self).get(request, *args, **kwargs)
            return super(BasicListActionView,self).get(request, *args, **kwargs)


class SimpleMarkingAdditionView(BasicListActionView):

    # Override the following parameters in views inheriting from this view.

    title = 'Mark objects'

    description = """Provide here a brief description for the user of what to do -- this will be displayed
                     in the view."""

    template_name = 'dingos/%s/actions/SimpleMarkingAdditionView.html' % DINGOS_TEMPLATE_FAMILY

    action_model_query = InfoObject.objects.all()

    def marked_obj_name_function(self,x):
        return x.name

    # Specify either a Django queryset or a DINGOS custom query that selects the marking objects
    # that will be offered in the view



    marking_queryset = None # InfoObject.objects.filter(iobject_type__name='Marking')


    marking_query = None# """object: object_type.name = 'Marking' && identifier.namespace contains 'cert.siemens.com'"""

    # The query with which possible marking objects are selected may potentially return many objects;
    # specify below, how many should be displayed.

    max_marking_choices=20

    allow_multiple_markings=False

    # The form inherits from the BasicListActionForm: we have added
    # the field for selecting marking objects

    form_class = SimpleMarkingAdditionForm



    # If True, marking is not actually applied
    debug_marking = False

    # If True, action is not actually carried out
    debug_action = False

    # Action List

    # Elements of the list should have the following form:
    # {'action_predicate': <function taking instance of marking object and objet to be marked,
    #                       returning True or False
    #                       whether action is to be carried out on the marked object>,
    #  'action_function': <function taking model instances of marking object and object to be
    #                      marked and carrying out action based on marked object. Should return
    #                         (True, 'Success message')
    #                      for successful execution or
    #                         (False, 'Error message')
    #                      for problem in executing action
    #  'mark_after_failure': True/False -- governs whether marking should be carried out
    #                      even if an error occured. Default is 'False', i.e., if the action
    #                      was not successful, the marking is not carried out.
    #  'action_for_existing_marking': True/False -- governs, whether action is to be carried out
    #                      even if marking already existed. Default is 'False'.
    # For each marking to be added, the list is traversed; the first action for which the
    # predicate returned True is carried out.


    action_before_marking_list = []

    # The following parameter governs, whether objects for which no action was found,
    # are marked or not.

    apply_marking_wo_action = True


    # If no action could be found (and 'apply_marking_wo_action' is set to False)
    # we return the following error message. Use this to provide the user with more
    # information about why you think that no actions could be found.

    no_action_error_message = "No valid action could be found for the object."

    @property
    def m_queryset(self):
        """
        Queryset for selecting possible markings, either taken directly from self.marking_queryset
        or created from self.marking_query
        """
        if self.marking_queryset:
            return self.marking_queryset.values_list('pk','name')[0:self.max_marking_choices]
        elif self.marking_query:
            parser = QueryParser()

            filter_collections = parser.parse(self.marking_query)



            # TODO: the code that does the processing of the query should not be here
            # but part of the filter_collections object. This is because the query may
            # also be used at other places (e.g. below in the MarkingsAction view
            # If the user defined a referenced_by-preprocessing

            # If the user defined a referenced_by-preprocessing

            objects = InfoObject.objects.all()

            if filter_collections.refby_filter_collection:
                # Preprocessing for referenced-by query
                refby_filter_collection = filter_collections.refby_filter_collection.filter_collection
                objects = refby_filter_collection.build_query(base=objects)
                objects = objects.distinct()
                # Retrieve pk list out of the object list
                pks = [one.pk for one in objects]
                pks = graph_traversal.follow_references(pks, **filter_collections.refby_filter_args)

                # Filter objects
                objects = self.query_base.all().filter(pk__in=pks)

            # Processing for main query
            formatted_filter_collection = filter_collections.formatted_filter_collection

            if hasattr(formatted_filter_collection, 'filter_collection'):
                objects = formatted_filter_collection.filter_collection.build_query(base=objects)


            self.marking_queryset = objects

            return self.marking_queryset.values_list('pk','name')[0:self.max_marking_choices]
        else:
            raise StandardError("You must provide a queryset or query.")

    def post(self, request, *args, **kwargs):

        # If this is the first time, the view is rendered, it has been
        # called as action from another view; in that case, there must be
        # the result of the multiple-choice field with which objects
        # to perform the action on were selected in the POST request.
        # So we use the presence of 'action_objects' to see whether
        # this is indeed the first call.

        if 'action_objects' in self.request.POST:

            self._set_initial_form(markings= self.m_queryset,
                                   allow_multiple_markings=self.allow_multiple_markings)
            return super(SimpleMarkingAdditionView,self).get(request, *args, **kwargs)
        else:
            # So the view has been called a second time by submitting the form in the view
            # rather than from a different view. So we need to process the data in the form

            self._set_post_form(request.POST,
                                markings = self.m_queryset,
                                allow_multiple_markings = self.allow_multiple_markings)

            # React on a valid form
            if self.form.is_valid():
                form_data = self.form.cleaned_data

                # For creating markings, we need to use the Django Content-Type mechanism

                content_type = ContentType.objects.get_for_model(self.action_model_query.model)

                if isinstance(form_data['marking_to_add'],list):
                    markings_to_add = form_data['marking_to_add']
                else:
                    markings_to_add = [form_data['marking_to_add']]

                for marking_pk in markings_to_add:

                    # Read out object with which marking is to be carried out
                    marking_obj = InfoObject.objects.get(pk=marking_pk)

                    # Create the markings
                    marked = []
                    skipped = []

                    for obj_pk in form_data['checked_objects']:

                        obj_to_be_marked = InfoObject.objects.get(pk=obj_pk)


                        action_list = self.action_before_marking_list
                        if self.apply_marking_wo_action:
                            # We add a catch-all action as last action that always succeeds
                            # Thus we do not need to write duplicate code outside the loop
                            # in cases where we wish to apply markings without having carried out
                            # an action.
                            action_list.append({'action_predicate': lambda x,y: True,
                                                'action_function': lambda x,y: (True,''),
                                                })
                        found_action = False
                        for action  in action_list:
                            if found_action:
                                break
                            action_predicate = action['action_predicate']
                            action_function = action['action_function']
                            mark_after_failure = action.get('mark_after_failure',False)
                            action_for_existing_marking = action.get('action_for_existing_marking',False)

                            if action_predicate(marking_obj,obj_to_be_marked):
                                found_action = True
                                try:
                                    existing_marking = Marking2X.objects.get(object_id=obj_pk,
                                                          content_type = content_type,
                                                          marking=marking_obj)
                                    existing_marking = True
                                except ObjectDoesNotExist:
                                    existing_marking = False
                                except MultipleObjectsReturned:
                                    existing_marking = True

                                if existing_marking and not action_for_existing_marking:
                                    message = """%s skipped, because it is already marked with '%s'.
                                                 No further action has been carried out.""" % (self.marked_obj_name_function(obj_to_be_marked),
                                                                             marking_obj.name,
                                                                             )
                                    messages.error(self.request,message)
                                    break

                                if self.debug_action:
                                    (success,action_msg) = (True,"DEBUG: Action has not been carried out")
                                else:
                                    (success,action_msg) = action_function(marking_obj,obj_to_be_marked)
                                if success or ((not success) and mark_after_failure):
                                    if self.debug_marking:
                                        created = not existing_marking
                                    else:
                                        marking2x, created = Marking2X.objects.get_or_create(object_id=obj_pk,
                                                                                             content_type = content_type,
                                                                                             marking=marking_obj)
                                    if created:
                                        message = """%s marked with %s. %s""" % (self.marked_obj_name_function(obj_to_be_marked),
                                                                                 marking_obj.name,
                                                                                 action_msg)
                                    else:
                                        message = """%s was already marked with %s. %s""" % (self.marked_obj_name_function(obj_to_be_marked),
                                                                                 marking_obj.name,
                                                                                 action_msg)

                                    if success:
                                        messages.success(self.request, message)
                                    else:
                                        messages.error(self.request, message)

                                else:
                                    message = """%s not marked with %s: %s""" % (self.marked_obj_name_function(obj_to_be_marked),
                                                                                 marking_obj.name,
                                                                                 action_msg)

                                    messages.error(self.request,message)
                        if not found_action:
                            message = """%s could not be marked: %s.""" % (self.marked_obj_name_function(obj_to_be_marked),
                                                                           self.no_action_error_message)
                            messages.error(self.request,message)


                #Clear checkboxes by emptying the corresponding parameter in the form data and
                #recreating the form object from this data

                form_data['checked_objects'] = []
                self._set_post_form(form_data,
                                    markings = self.m_queryset,
                                    allow_multiple_markings= self.allow_multiple_markings)


                return super(SimpleMarkingAdditionView,self).get(request, *args, **kwargs)
            return super(SimpleMarkingAdditionView,self).get(request, *args, **kwargs)


def processTagging(data,**kwargs):

    TAG_HTML =  """
                <span id="%s" class="tag stay-inline">
                    <a href="%s" class="stay-inline">%s</a>
                    <a class="remove_tag_button stay-inline" data-tag-name="%s"> X</a>
                </span>
                """

    #TODO bulk variante

    def _preprocess_tags(tags):
        if isinstance(tags,set):
            tags = list(tags)
        else:
            tags = listify(tags)

        possible_tag_types = {
            str : lambda tags: tags,
            unicode : lambda tags: tags,
            int : lambda tags: Tag.objects.filter(id__in=tags).values_list('name',flat=True)
        }
        type = tags[0].__class__
        preprocess = possible_tag_types.get(type,None)
        if preprocess is None:
            raise TypeError("%s not a possible type for tags - possible types are %s") % (type,possible_tag_types.keys())
        tags = preprocess(tags)

        not_allowed = []
        if TAGGING_REGEX:
            for tag in tags:
                if not any(regex.match(tag) for regex in TAGGING_REGEX):
                    not_allowed.append(tag)
                    tags.remove(tag)

        return tags,not_allowed

    action = data['action']
    obj_pks = data['objects']
    obj_type = data['obj_type']
    tags = listify(data['tag_names'])
    print "Passed tags %s" % tags

    res = {}
    ACTIONS = ['add', 'remove']
    if action in ACTIONS:
        tags_to_add,not_allowed_tags = _preprocess_tags(tags)
        model = dingos_class_map.get(obj_type,None)
        if model is None:
            raise ObjectDoesNotExist('no suitable model found named %s') % (model)
        user = kwargs.pop('user',None)
        if user is None or not isinstance(user,User):
            raise ObjectDoesNotExist('no user for this action provided')

        objects = list(model.objects.filter(pk__in=obj_pks))
        user_data = data.get('user_data',None)

        if tags_to_add:
            if action == 'add':
                for object in objects:
                    object.tags.add(*tags_to_add)
                    if not kwargs['bulk']:
                        tag = tags_to_add[0]
                        url = urlresolvers.reverse('url.dingos.tagging.tagged_things',args=[tag])
                        res['html'] = TAG_HTML % (tag,url,tag,tag)
                        res['status'] = 0
                    else:
                        pass
                        #TODO bulk
                comment = '' if not user_data else user_data
                TaggingHistory.bulk_create_tagging_history(action,tags_to_add,objects,user,comment)

            elif action == 'remove':
                if user_data is None:
                    res['additional'] = {
                        'dialog_id' : 'dialog-tagging-remove',
                        'msg' : 'To delete this tag, enter a comment on this action here.'
                    }
                    res['status'] = 1
                else:
                    if user_data == '':
                        res['status'] = -1
                        res['err'] = "no comment provided - tag not deleted"
                    else:
                        for object in objects:
                            object.tags.remove(*tags_to_add)
                        TaggingHistory.bulk_create_tagging_history(action,tags_to_add,objects,user,user_data)
                        res['status'] = 0
        else:
            res['err'] = "tag not allowed: %s" % (not_allowed_tags)
            res['status'] = -1
    else:
        raise NotImplementedError('%s not a possible action to perform') % (action)

    return res


class TaggingAdditionView(BasicListActionView):

    # Override the following parameters in views inheriting from this view.

    title = 'Tag objects'

    description = """Allows the user to add tags to multiple infoobjects at once."""

    template_name = 'dingos/%s/actions/TagingAdditionView.html' % DINGOS_TEMPLATE_FAMILY

    action_model_query = None

    #select tag objects
    tagging_queryset = Tag.objects.all().values_list('pk','name')

    allow_multiple_tags=True
    form_class = TaggingAdditionForm

    action_list = []
    action_list.append({'action_predicate': lambda x : True,
                        'action_function': processTagging})

    def post(self, request, *args, **kwargs):
        self.type = request.POST.get('type', None)
        self.model_class = dingos_class_map.get(self.type,None)
        if not self.model_class:
            raise ObjectDoesNotExist("dingos model class does not exist: %s - check if there is a hidden type input field in html" % (self.type))
        self.action_model_query = self.model_class.objects.all()

        if 'action_objects' in request.POST:
            self._set_initial_form(tags=self.tagging_queryset,allow_multiple_tags=self.allow_multiple_tags)
            return super(TaggingAdditionView,self).get(request, *args, **kwargs)

        else:
            self._set_post_form(tags=self.tagging_queryset,allow_multiple_tags=self.allow_multiple_tags)

            # React on a valid form
            if self.form.is_valid():
                form_data = self.form.cleaned_data
            else:
                return super(TaggingAdditionView,self).get(request, *args, **kwargs)
            found_action = False
            for action in self.action_list:
                if found_action:
                    break
                action_predicate = action['action_predicate']
                action_function = action['action_function']

                if action_predicate(True):
                    found_action = True

                    if self.debug_action:
                        (success,action_msg) = (True,"DEBUG: Action has not been carried out")
                    else:
                        action = request.POST['action'].split(" ")[0].lower()
                        if action == 'remove' and form_data['comment'] == '':
                            messages.error(self.request,"A comment must be provided in order to delete tags!")

                        else:
                            if self.type == 'InfoObject':
                                objects = Identifier.objects.filter(iobject_set__id__in=form_data['checked_objects']).distinct('id').values_list('id',flat=True)
                                curr_type = 'Identifier'
                            else:
                                objects = [int(x) for x in form_data['checked_objects']]
                                curr_type = self.type
                            action_function(action,objects,curr_type,[int(x) for x in form_data['tag_to_add']],user=request.user,comment=form_data['comment'])
            if not found_action:
                message = self.no_action_error_message
                messages.error(self.request,message)

                #Clear checkboxes by emptying the corresponding parameter in the form data and
                #recreating the form object from this data

                form_data['checked_objects'] = []
                self._set_post_form(form_data,
                                    tags=self.tagging_queryset,
                                    allow_multiple_tags=self.allow_multiple_tags)

                return super(TaggingAdditionView,self).get(request, *args, **kwargs)
            return super(TaggingAdditionView,self).get(request, *args, **kwargs)

    def fact_by_pk(self,pk):
        for f in self.object_list:
            if "%s" % f.pk == "%s" % pk:
                return f
        return None


class TagHistoryView(BasicTemplateView):
    template_name = 'dingos/%s/lists/TagHistoryList.html' % DINGOS_TEMPLATE_FAMILY

    title = 'Tag History'

    tag = None

    possible_models = {
            Fact : ['id','fact_term__term','fact_term__attribute','fact_values__value'],
            Identifier : ['id','latest__name','uid','latest__id','namespace__uri']
        }

    def get_context_data(self, **kwargs):
        context = super(TagHistoryView, self).get_context_data(**kwargs)

        cols_history = ['tag__name','timestamp','action','user__username','content_type_id','object_id','comment']
        sel_rel = ['tag','user','content_type']
        if self.mode == 'contains':
            history_q = list(TaggingHistory.objects.select_related(*sel_rel).filter(tag__name__contains=self.tag).order_by('timestamp').values(*cols_history))
        else:
            history_q = list(TaggingHistory.objects.select_related(*sel_rel).filter(tag__name=self.tag).order_by('timestamp').values(*cols_history))

        obj_info_mapping = {}
        for model,cols in self.possible_models.items():
            content_id = ContentType.objects.get_for_model(model).id
            setattr(self,'pks',set([x['object_id'] for x in history_q if x['content_type_id'] == content_id]))
            model_q = model.objects.filter(id__in=self.pks).values(*cols)
            current_model_map = obj_info_mapping.setdefault(content_id,{})
            for obj in model_q:
                current_model_map[obj['id']] = obj
            del self.pks
        context['mode'] = self.mode
        context['tag'] = self.tag
        context['history'] = history_q
        context['map_objs'] = obj_info_mapping
        context['map_action'] = TaggingHistory.ACTIONS
        return context

    def get(self, request, *args, **kwargs):
        self.mode = request.GET.get('mode')
        self.tag = kwargs.pop('tag',None)
        if self.mode == 'contains':
            self.title = "Timeline for tags containing string '%s'" % self.tag
        else:
            self.title = "Timeline for tag '%s'" % self.tag
        return super(TagHistoryView,self).get(request, *args, **kwargs)

from dingos.templatetags.dingos_tags import reachable_packages
class TaggedObjectsView(BasicTemplateView):
    template_name = 'dingos/%s/lists/TaggedObjectsList.html' % DINGOS_TEMPLATE_FAMILY

    title = 'Tagged Items'

    tag = None

    possible_models = {
            Fact : ['fact_term__term','fact_term__attribute','fact_values__value'],
            Identifier : ['latest__name','uid','latest__id']
        }

    def get_context_data(self, **kwargs):
        context = super(TaggedObjectsView, self).get_context_data(**kwargs)
        model_objects_mapping =  {}

        if self.mode == 'contains':
            tag_id = Tag.objects.filter(name__contains=self.tag).values_list('id',flat=True)
        else:
            tag_id = [Tag.objects.get(name=self.tag).id]
        for model,cols in self.possible_models.items():
            if model == Fact and self.display == 'factdetails':
                cols = ['term','attribute','value','iobject_id','fact_id']
                matching_items_tmp = list(vIO2FValue.objects.filter(fact__tag_through__tag__id__in = tag_id).values(*cols))

                matching_items = set()

                fact2parent = {}
                parent2toplevel = {}
                iobj2nodeinfo = {}
                parent_iobj_pks = set()


                for x in matching_items_tmp:
                    parent_list = fact2parent.setdefault(x['fact_id'],[])
                    parent_list.append(x['iobject_id'])
                    parent_iobj_pks.add(x['iobject_id'])
                    row = (x['term'],x['attribute'],x['value'],x['fact_id'])
                    matching_items.add(row)

                context['object_list'] = list(parent_iobj_pks)
                for parent_pk in parent_iobj_pks:
                    found_top_level_objects = reachable_packages(context,parent_pk)['node_list']
                    top_list = parent2toplevel.setdefault(parent_pk,[])
                    for (pk,node_info) in found_top_level_objects:
                        top_list.append(pk)
                        if not pk in iobj2nodeinfo.keys():
                            iobj2nodeinfo[pk] = (node_info['identifier_ns'],node_info['identifier_uid'],node_info['name'])

                #retrieve missing iobj infos
                no_info = parent_iobj_pks - set(iobj2nodeinfo.keys())
                infos = vIO2FValue.objects.filter(iobject_id__in=no_info).distinct('iobject_id').values('iobject_id','iobject_identifier_uri','iobject_identifier_uid','iobject_name')
                for x in infos:
                    iobj2nodeinfo[x['iobject_id']] = (x['iobject_identifier_uri'],x['iobject_identifier_uid'],x['iobject_name'])

                context['fact2parent'] = fact2parent
                context['parent2toplevel'] = parent2toplevel
                context['iobj2nodeinfo'] = iobj2nodeinfo

            else:
                matching_items = list(model.objects.filter(tag_through__tag__id__in = tag_id).distinct('id').values_list(*cols))
            print "-------"
            print model
            print matching_items
            model_objects_mapping[model.__name__] = matching_items

        context['tag'] = self.tag
        context['model_objects_mapping'] = model_objects_mapping

        for x in model_objects_mapping.get('Fact',[]):
            print x

        return context

    def get(self, request, *args, **kwargs):
        self.display = request.GET.get('display')
        self.mode = request.GET.get('mode')
        self.tag = kwargs.pop('tag')
        return super(TaggedObjectsView,self).get(request, *args, **kwargs)
