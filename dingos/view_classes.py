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


class CommonContextMixin(ContextMixin):
    def get_context_data(self, **kwargs):
        context = super(CommonContextMixin, self).get_context_data(**kwargs)
        context['title'] = self.title if hasattr(self, 'title') else '[TITLE MISSING]'

        ######## user customization
        # there are four cases if settings exist within session scope:
        # 1.) unauthenticated user && non-anonymous settings --> load
        # 2.) unauthenticated user && anonymous settings --> pass
        # 3.) authenticated user && non-anonymous settings --> pass
        # 4.) authenticated user && anonymous settings --> load

        settings = self.request.session.get('customization')
        saved_searches = self.request.session.get('saved_searches')
        load_new_settings = False

        if settings:

            # case 1.)
            if not self.request.user.is_authenticated() and self.request.session.get('customization_for_authenticated'):
                load_new_settings = True

            # case 4.)
            elif self.request.user.is_authenticated() and not self.request.session.get('customization_for_authenticated'):
                load_new_settings = True

        else:
            load_new_settings = True

        if True:
            # Load user settings. If for the current user, no user settings have been
            # stored, retrieve the default settings and store them (for authenticated users)

            self.request.session['customization_for_authenticated']=self.request.user.is_authenticated()

            settings = UserData.get_user_data(user=self.request.user,data_kind=DINGOS_USER_PREFS_TYPE_NAME)
            if not settings:
                settings = copy.deepcopy(DINGOS_DEFAULT_USER_PREFS)
                if self.request.user.is_authenticated():
                    UserData.store_user_data(user=self.request.user,data_kind=DINGOS_USER_PREFS_TYPE_NAME,user_data=settings)

            self.request.session['customization']=settings


            # Do the same for saved searches

            saved_searches = UserData.get_user_data(user=self.request.user,data_kind=DINGOS_SAVED_SEARCHES_TYPE_NAME)
            if not saved_searches:
                saved_searches = copy.deepcopy(DINGOS_DEFAULT_SAVED_SEARCHES)
                if self.request.user.is_authenticated():
                    UserData.store_user_data(user=self.request.user,
                                             data_kind=DINGOS_SAVED_SEARCHES_TYPE_NAME,
                                             user_data=saved_searches)

            self.request.session['saved_searches']=saved_searches
            #context['customization'] = ConfigDictWrapper(config_dict={'searches':{'blah':5}})

        context['customization'] = ConfigDictWrapper(config_dict=settings)
        context['saved_searches'] = ConfigDictWrapper(config_dict=saved_searches)

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
    def read_config(self,*args,**kwargs):
        return "%s with default %s" % (','.join(args),kwargs.get('default',None))

class BasicListView(CommonContextMixin,ViewMethodMixin,LoginRequiredMixin,ListView):

    login_url = "/admin"

    template_name = 'dingos/%s/lists/base_lists_two_column.html' % DINGOS_TEMPLATE_FAMILY

    breadcrumbs = ()

    paginate_by = 20

class BasicFilterView(CommonContextMixin,ViewMethodMixin,LoginRequiredMixin,FilterView):

    login_url = "/admin"

    template_name = 'dingos/%s/lists/base_lists_two_column.html' % DINGOS_TEMPLATE_FAMILY

    breadcrumbs = ()

    paginate_by = 20

class BasicDetailView(CommonContextMixin,
                      ViewMethodMixin,
                      LoginRequiredMixin,
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


