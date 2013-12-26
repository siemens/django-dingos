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

from django.views.generic.base import ContextMixin
from django.views.generic import DetailView, ListView, TemplateView

from braces.views import LoginRequiredMixin, SelectRelatedMixin,PrefetchRelatedMixin
from core.http_helpers import get_query_string

from django_filters.views import FilterView

from dingos.models import get_user_settings
from dingos import DINGOS_TEMPLATE_FAMILY


class ConfigDict(object):
    """
    A helper class for using customized 
    configurations within django views
    """

    _orig_dict =  None
    _stack = []

    def __init__(self, orig_dict):
        """
        Needs to receive a dict-like object for init.
        Note that it works with all dict-like objects WITHOUT a boolean as key!
        """
        self._orig_dict = orig_dict
        
    def get(self, key):
        """ Just a wrapper for __getitem__() """
        return self.__getitem__(key)

    def _clear_stack(self):
        """ Just clears the stack and returns it's last value (centralized method) """
        out = self._stack[len(self._stack)-1]
        self._stack = []
        return out

    def __getitem__(self, key):
        """
        Returns itself until a "True" is given as key (as String instance).
        In this very case all the former called keys are being tried.
        If the path turns out to return a valid object it is returned.
        Otherwise the SECOND LAST key argument (the one BEFORE bool) will
        be returned as it represents the default value. 

        Example usage:
          this_dict = ConfigDict({ 'first' : { 'second' : 20 } })
          this_dict.get('first').get('second').get(1).get("True")
          returns 20 instead of the 1 (which represents the default value)
        """

        # no bool? just append element and return yourself
        if not key == "True":
            self._stack.append(key) 
            return self

        print self._stack
        # time to create an output by going along stack (last element of stack is DEFAULT value!)
        current_element = self._orig_dict
        for i in range(0, len(self._stack)-1):
            try:
                current_element = current_element[self._stack[i]]

            # exception raised (TypeError or KeyError)? Return default value
            except Exception as e:
                return self._clear_stack()

        return self._clear_stack()


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
        load_new_settings = False

        if settings:

            # case 1.)
            if not self.request.user.is_authenticated() and not settings.get('anonymous'):
                load_new_settings = True

            # case 4.)
            elif self.request.user.is_authenticated() and settings.get('anonymous'):
                load_new_settings = True

        else:
            load_new_settings = True

        if True: #load_new_settings:
            context['customization'] = ConfigDict(get_user_settings(self.request.user))
            print(context['customization']._orig_dict)

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


