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
    url(r'^View/InfoObject/(?P<pk>\d*)/json$',
        views.InfoObjectJSONView.as_view(),
        name= "url.dingos.view.infoobject.json"),
    url(r'^Search/SimpleFactSearch$',
        views.SimpleFactSearch.as_view(),
        name="url.dingos.search.fact.simple"),
    url(r'^Search/IdSearch$',
        views.InfoObjectList_Id_filtered.as_view(),
        name="url.dingos.list.infoobject.by_id"),

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
