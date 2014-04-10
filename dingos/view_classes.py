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


import csv

import collections
import copy
import json

from django import http


from django.views.generic.base import ContextMixin
from django.views.generic import DetailView, ListView, TemplateView, View

from django.core.paginator import Paginator, EmptyPage

from django.core.paginator import PageNotAnInteger


from django.db import DataError


from django.shortcuts import render_to_response

from braces.views import LoginRequiredMixin, SelectRelatedMixin,PrefetchRelatedMixin

from  django.core import urlresolvers

from django.contrib import messages

from django.utils.http import urlquote_plus

from core.http_helpers import get_query_string

from django.http import HttpResponseRedirect, HttpResponse



from django_filters.views import FilterView

from braces.views import LoginRequiredMixin, SelectRelatedMixin,PrefetchRelatedMixin

from dingos.models import UserData

from dingos.forms import CustomQueryForm

from dingos.queryparser.result_formatting import to_csv

from dingos import DINGOS_TEMPLATE_FAMILY, \
    DINGOS_USER_PREFS_TYPE_NAME, \
    DINGOS_DEFAULT_USER_PREFS, \
    DINGOS_SAVED_SEARCHES_TYPE_NAME, \
    DINGOS_DEFAULT_SAVED_SEARCHES, \
    DINGOS_QUERY_PREFETCH_RELATED_MAPPING

from dingos.core.template_helpers import ConfigDictWrapper

from dingos.core.utilities import get_dict, replace_by_list

from dingos.models import InfoObject

from queryparser.queryparser import QueryParser


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

    def get_user_data(self):
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
        load_new_settings = False

        if settings:

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


class BasicListView(CommonContextMixin,ViewMethodMixin,LoginRequiredMixin,ListView):
    """
    Basic class for defining list views: includes the necessary mixins
    and code to read pagination information from user customization.
    """


    login_url = "/admin"

    template_name = 'dingos/%s/lists/base_lists_two_column.html' % DINGOS_TEMPLATE_FAMILY

    breadcrumbs = ()

    counting_paginator = False

    @property
    def paginator_class(self):
        if not self.counting_paginator:
            return UncountingPaginator
        else:
            return super(BasicFilterView,self).paginator_class

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

    counting_paginator = False

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
                "parameter" : "&".join(list( "%s=%s" % (urlquote_plus(k),urlquote_plus(v)) for k, v in request.GET.iteritems() if v and k != "action")),
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

    counting_paginator = False

    template_name = 'dingos/%s/searches/CustomInfoObjectSearch.html' % DINGOS_TEMPLATE_FAMILY

    title = 'Custom Info Object Search'

    form = None
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
        context['col_headers'] = self.col_headers
        context['selected_cols'] = self.selected_cols
        return context

    def get(self, request, *args, **kwargs):
        self.form = CustomQueryForm(request.GET)
        self.queryset = []

        if 'execute_query' in request.GET and self.form.is_valid():
            if request.GET['query'] == "":
                messages.error(self.request, "Please enter a query.")
            else:
                try:
                    # Parse query
                    parser = QueryParser()
                    query = self.form.cleaned_data['query']
                    self.paginate_by_value = int(self.form.cleaned_data['paginate_by'])
                    if self.form.cleaned_data['page']:
                        self.page_to_show = int(self.form.cleaned_data['page'])

                    # Generate and execute query
                    formatted_filter_collection = parser.parse(str(query))

                    filter_collection = formatted_filter_collection.filter_collection

                    objects = self.query_base.all()
                    objects = filter_collection.build_query(base=objects)

                    if self.distinct:
                        if isinstance(self.distinct, tuple):
                            objects = objects.order_by(*list(self.distinct)).distinct(*list(self.distinct))
                        elif self.distinct:
                            objects = objects.distinct()
                        else:
                            raise TypeError("'distinct' must either be True or a tuple of field names.")

                    # Output format
                    result_format = formatted_filter_collection.format

                    # Filter selected columns for export
                    col_specs = formatted_filter_collection.col_specs
                    misc_args = formatted_filter_collection.misc_args

                    if self.prefetch_related:
                        if isinstance(self.prefetch_related, tuple):
                            ## Prefetch displayed columns (they are needed in any case)
                            #display_cols = col_specs['selected_fields']
                            #filtered_cols = tuple()
                            #for col in display_cols:
                            #    filtered_col = replace_by_list(col, DINGOS_QUERY_PREFETCH_RELATED_MAPPING)
                            #    if not filtered_col == '':
                            #        filtered_cols = filtered_cols + (filtered_col,)

                            #self.prefetch_related = self.prefetch_related + tuple(filtered_cols)
                            ## Remove duplicate items
                            #self.prefetch_related = tuple(set(self.prefetch_related))

                            objects = objects.prefetch_related(*list(self.prefetch_related))
                        else:
                            raise TypeError("'prefetch_related' must either be True or a tuple of field names.")

                    self.queryset = objects

                    if result_format == 'default':
                        # Pretty useless case for live system but useful for tests
                        return super(BasicListView, self).get(request, *args, **kwargs)
                    elif result_format == 'csv':
                        p = self.paginator_class(self.queryset, self.paginate_by_value)
                        response = HttpResponse(content_type='text') # '/csv')
                        #response['Content-Disposition'] = 'attachment; filename="result.csv"'
                        writer = csv.writer(response)

                        to_csv(p.page(self.page_to_show).object_list,
                               writer,
                               col_specs['headers'],
                               col_specs['selected_fields'],
                               **misc_args)

                        return response
                    elif result_format == 'table':
                        self.col_headers = col_specs['headers']
                        self.selected_cols = col_specs['selected_fields']
                        return super(BasicListView, self).get(request, *args, **kwargs)
                    else:
                        raise ValueError('Unsupported output format')

                except DataError as ex:
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




