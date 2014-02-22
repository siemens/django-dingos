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


from django.conf.urls import patterns, url
from django.core.urlresolvers import reverse
from django.shortcuts import redirect

from dingos import views
from dingos import filter
from dingos.models import InfoObject

from django_filters.views import FilterView

urlpatterns = patterns('',
    url(r'^View/InfoObject/?$',
        views.InfoObjectList.as_view(),
        name="url.dingos.list.infoobject.generic"),
    url(r'^View/InfoObject/(?P<pk>\d*)/$',
        views.InfoObjectView.as_view(),
        name= "url.dingos.view.infoobject"),
    url(r'^Admin/ViewUserPrefs/?$',
        views.UserPrefsView.as_view(),
        name= "url.dingos.admin.view.userprefs"),
    url(r'^View/InfoObject/(?P<pk>\d*)/json$',
        views.InfoObjectJSONView.as_view(),
        name= "url.dingos.view.infoobject.json"),
    url(r'^Search/SimpleFactSearch$',
        views.SimpleFactSearch.as_view(),
        name="url.dingos.search.fact.simple"),
    url(r'^Search/UniqueSimpleFactSearch$',
        views.UniqueSimpleFactSearch.as_view(),
        name="url.dingos.search.fact.simple.unique"),
    url(r'^Search/IdSearch$',
        views.InfoObjectList_Id_filtered.as_view(),
        name="url.dingos.list.infoobject.by_id"),
    url(r'^Edit/SavedSearches$',
        views.CustomSearchesEditView.as_view(),
        name="url.dingos.admin.edit.savedsearches"),

    # Uncommenting below enables an edit view for InfoObjects
    # that will overwrite an InfoObject without creating an
    # new revision!!!
    #url(r'^Edit/InfoObject/(?P<pk>\d*)/$',
    #    views.InfoObjectsEditView.as_view(),
    #    name="url.dingos.admin.edit.infoobject"),

    # Detail-view with highlight and anchor on certain node
    # solved below with a redirect, because with the 'url' template
    # tag we cannot set an anchor.
    url(r'^View/InfoObject/(?P<pk>\d*)/(?P<node>([A-Z]\d{3,4})?(:[A-Z]\d{3,4})*)/',
        lambda *args, **kwargs: redirect( 
            reverse( 'url.dingos.view.infoobject',
                      kwargs = { 'pk' : int(kwargs['pk']) } ) + '?highlight=%(node)s#%(node)s' % kwargs,
            permanent = True
            ),
        name = 'url.dingos.view.infoobject.redirect2highlight'
    ),

    url(r'^View/InfoOject/Embedded/(?P<pk>\d*)/$', views.InfoObjectsEmbedded.as_view(), name="url.dingos.view.infoobject.embedded"),

    )
