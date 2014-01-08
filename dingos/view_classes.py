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

import collections
import copy

from django.views.generic.base import ContextMixin
from django.views.generic import DetailView, ListView, TemplateView

from braces.views import LoginRequiredMixin, SelectRelatedMixin,PrefetchRelatedMixin
from core.http_helpers import get_query_string

from django_filters.views import FilterView

from dingos.models import UserData
from dingos import DINGOS_TEMPLATE_FAMILY, \
    DINGOS_USER_PREFS_TYPE_NAME, \
    DINGOS_DEFAULT_USER_PREFS, \
    DINGOS_SAVED_SEARCHES_TYPE_NAME, \
    DINGOS_DEFAULT_SAVED_SEARCHES

from dingos.core.template_helpers import ConfigDictWrapper

from dingos.core.utilities import get_dict

class CommonContextMixin(ContextMixin):
    """
    Each view passes a 'context' to the template with which the view
    is rendered. By inluding this mixin in a class-based view, the
    context is enriched with the contents expected by all Dingos
    templates.
    """
    def get_context_data(self, **kwargs):
        context = super(CommonContextMixin, self).get_context_data(**kwargs)

        context['title'] = self.title if hasattr(self, 'title') else '[TITLE MISSING]'


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

        wrapped_settings = ConfigDictWrapper(config_dict=user_data_dict.get('customization',{}))
        wrapped_saved_searches = ConfigDictWrapper(config_dict=user_data_dict.get('saved_searches',{}))

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

            self.request.session['customization_for_authenticated']=self.request.user.is_authenticated()



            settings = UserData.get_user_data(user=self.request.user,data_kind=DINGOS_USER_PREFS_TYPE_NAME)
            if not settings:
                UserData.store_user_data(user=self.request.user,data_kind=DINGOS_USER_PREFS_TYPE_NAME,user_data=DINGOS_DEFAULT_USER_PREFS)
                settings = UserData.get_user_data(user=self.request.user,data_kind=DINGOS_USER_PREFS_TYPE_NAME)



            # Do the same for saved searches

            saved_searches = UserData.get_user_data(user=self.request.user, data_kind=DINGOS_SAVED_SEARCHES_TYPE_NAME)
            if not saved_searches:

                UserData.store_user_data(user=self.request.user,
                                         data_kind=DINGOS_SAVED_SEARCHES_TYPE_NAME,
                                         user_data=DINGOS_DEFAULT_SAVED_SEARCHES)
                saved_searches = UserData.get_user_data(user=self.request.user, data_kind=DINGOS_SAVED_SEARCHES_TYPE_NAME)



            self.request.session['customization'] = settings
            self.request.session['saved_searches'] = saved_searches

        return {'customization': settings,
                'saved_searches' : saved_searches}


    def lookup_customization(self,*args,**kwargs):
        user_data = self.get_user_data()
        default_value = kwargs['default']

        result =  get_dict(user_data.get('customization',{}),*args,**kwargs)
        try:
            result = int(result)
        except:
            pass

        if not isinstance(result,default_value.__class__):
            return default_value
        else:
            return result


class BasicListView(CommonContextMixin,ViewMethodMixin,LoginRequiredMixin,ListView):

    login_url = "/admin"

    template_name = 'dingos/%s/lists/base_lists_two_column.html' % DINGOS_TEMPLATE_FAMILY

    breadcrumbs = ()

    @property
    def paginate_by(self):
        item_count = self.lookup_customization('dingos','view','pagination','lines',default=20)
        return item_count

class BasicFilterView(CommonContextMixin,ViewMethodMixin,LoginRequiredMixin,FilterView):

    login_url = "/admin"

    template_name = 'dingos/%s/lists/base_lists_two_column.html' % DINGOS_TEMPLATE_FAMILY

    breadcrumbs = ()

    @property
    def paginate_by(self):
        return self.lookup_customization('dingos','view','pagination','lines',default=20)

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


class BasicTemplateView(CommonContextMixin,
                       ViewMethodMixin,
                       LoginRequiredMixin,
                       TemplateView):

    login_url = "/admin"


    breadcrumbs = (('Dingo',None),
                   ('View',None),
    )


