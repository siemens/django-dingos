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

from django import forms, http
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core import urlresolvers
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.paginator import PageNotAnInteger, Paginator, EmptyPage
from django.db import DataError
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.utils.http import urlquote_plus
from django.views.generic import DetailView, ListView, TemplateView, View
from django.views.generic.base import ContextMixin
from django_filters.views import FilterView

from braces.views import LoginRequiredMixin, SelectRelatedMixin,PrefetchRelatedMixin

from dingos import DINGOS_TEMPLATE_FAMILY, \
                   DINGOS_USER_PREFS_TYPE_NAME, \
                   DINGOS_DEFAULT_USER_PREFS, \
                   DINGOS_SAVED_SEARCHES_TYPE_NAME, \
                   DINGOS_DEFAULT_SAVED_SEARCHES,\
                   DINGOS_SEARCH_POSTPROCESSOR_REGISTRY

from dingos import graph_traversal
from dingos.core.template_helpers import ConfigDictWrapper
from dingos.core.utilities import get_dict, replace_by_list
from dingos.forms import CustomQueryForm, BasicListActionForm, SimpleMarkingAdditionForm, PlaceholderForm
from dingos.queryparser.placeholder_parser import PlaceholderParser
from dingos.models import InfoObject, UserData, Marking2X
from dingos.queryparser.result_formatting import to_csv

from core.http_helpers import get_query_string

POSTPROCESSOR_REGISTRY = {}


for (postprocessor_key,postprocessor_data) in DINGOS_SEARCH_POSTPROCESSOR_REGISTRY.items():
    my_module = importlib.import_module(postprocessor_data['module'])
    POSTPROCESSOR_REGISTRY[postprocessor_key] = getattr(my_module,postprocessor_data['class'])


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



    login_url = "/admin"

    template_name = 'dingos/%s/lists/base_lists_two_column.html' % DINGOS_TEMPLATE_FAMILY

    breadcrumbs = ()

    counting_paginator = True

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

    - read pagination information from user customization.
    - save filter settings as saved search
    """

    login_url = "/admin"

    template_name = 'dingos/%s/lists/base_lists_two_column.html' % DINGOS_TEMPLATE_FAMILY

    breadcrumbs = ()

    counting_paginator = True

    graph = None

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
        if request.GET.get('action','Submit Query') == 'Submit Query':
            return super(BasicFilterView,self).get(request, *args, **kwargs)
        else:
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

    login_url = "/admin"

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

    login_url = "/admin"


    breadcrumbs = (('Dingo',None),
                   ('View',None),
    )



class BasicCustomQueryView(BasicListView):
    page_to_show = 1

    counting_paginator = True

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
            if request.GET.get('query','') == "":
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



                    parser = QueryParser()
                    self.paginate_by_value = int(self.form.cleaned_data['paginate_by'])
                    if self.form.cleaned_data['page']:
                        self.page_to_show = int(self.form.cleaned_data['page'])

                    # Generate and execute queries

                    filter_collections = parser.parse(str(query))


                    objects = self.query_base.all()

                    # If the user defined a referenced_by-preprocessing
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
                    filter_collection = formatted_filter_collection.filter_collection

                    objects = filter_collection.build_query(base=objects)

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

                    if result_format == 'default':
                        return super(BasicListView, self).get(request, *args, **kwargs)

                    if result_format in POSTPROCESSOR_REGISTRY:
                        p = self.paginator_class(self.queryset, self.paginate_by_value)
                        response = HttpResponse(content_type='text') # '/csv')

                        #postprocessor_class = POSTPROCESSOR_REGISTRY[result_format]
                        #postprocessor = postprocessor_class(object_list=p.page(self.page_to_show).object_list)


                        postprocessor = formatting_arguments['postprocessor']
                        if postprocessor.query_mode == 'InfoObject':
                            postprocessor.object_list = p.page(self.page_to_show).object_list
                            postprocessor.initialize_object_details()
                        else:
                            postprocessor.io2fs = p.page(self.page_to_show).object_list


                        (content_type,result) = postprocessor.export(*col_specs['selected_fields'],
                                                                    **misc_args)

                        if result_format == 'table':
                            self.results = result
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
                    messages.error(self.request, str(ex))
        return super(BasicListView, self).get(request, *args, **kwargs)

class BasicJSONView(CommonContextMixin,
                    ViewMethodMixin,
                    LoginRequiredMixin,
                    View):

    login_url = "/admin"

    indent = 2

    @property
    def returned_obj(self):
        return {"This":"That"}

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


    def render_to_response(self, context):
        returned_obj = self.returned_obj
        if isinstance(returned_obj,basestring):
            json_string = returned_obj
        else:
            json_string = json.dumps(returned_obj,indent=self.indent)

        return self._get_json_response(json_string)



    def _get_json_response(self, content, **httpresponse_kwargs):
         return http.HttpResponse(content,
                                  content_type='application/json',
                                  **httpresponse_kwargs)


class BasicView(CommonContextMixin,
                ViewMethodMixin,
                LoginRequiredMixin,
                View):

    login_url = "/admin"



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
        object_set= self.request.POST.getlist('action_objects')
        if self.preprocess_action_objects:
            object_set = self.preprocess_action_objects(object_set)
        self.queryset = self.action_model_query.filter(pk__in = object_set)
        # We create the form
        kwargs['checked_objects_choices'] = object_set
        self.form = self.form_class({# We need a way to remember all objects that can be selected;
                                               # for this, we abuse a hidden field in which we collect a list
                                               # of object pks.
                                               'checked_objects_choices': ','.join(object_set),
                                               # We also preset all objects as checked
                                               'checked_objects' : object_set},
                                              # The parameters below are used to create the field for
                                              # selecting marking objects and the multiple choice field
                                              # for selecting objects.
                                              *args,
                                              **kwargs)


    def _set_post_form(self,*args,**kwargs):
        object_set =  self.request.POST.dict().get('checked_objects_choices').split(',')

        # Set the queryset for redisplaying the view with these objects

        self.queryset = self.action_model_query.filter(pk__in = object_set)

        kwargs['checked_objects_choices'] = object_set

        # Create the form object, this time from the POST data
        self.form = self.form_class(
                                    *args,
                                    **kwargs)

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

    marking_queryset = None

    marking_query = None # """object: object_type.name = 'Marking' && identifier.namespace contains 'cert.siemens.com'"""

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
            formatted_filter_collection = parser.parse(self.marking_query)
            filter_collection = formatted_filter_collection.filter_collection

            base_query = InfoObject.objects.all()
            self.marking_queryset = filter_collection.build_query(base=base_query)

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


