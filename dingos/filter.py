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


import django_filters

from collections import OrderedDict
from dingos.models import InfoObject, InfoObject2Fact, InfoObjectType, InfoObjectFamily,IdentifierNameSpace
from django.db.models import Count

from django.forms.models import ModelChoiceField

from django.utils.translation import ugettext_lazy as _

from datetime import timedelta
from django.utils.timezone import now

from dingos import DINGOS_INTERNAL_IOBJECT_FAMILY_NAME, DINGOS_ID_NAMESPACE_URI

_truncate = lambda dt: dt.replace(hour=0, minute=0, second=0)

def create_order_keyword_list(keywords):
    """
    Takes a given keyword list and returns a ready-to-go
    list of possible ordering values.

    Example: ['foo'] returns [('foo', ''), ('-foo', '')]
    """ 
    result = []
    for keyword in keywords:
        result.append((keyword, ''))
        result.append(('-%s' % keyword, ''))
    return result

class ExtendedDateRangeFilter(django_filters.DateRangeFilter):
    options = OrderedDict([
        ('', (_('Any date'), lambda qs, name: qs.all())),
        (100, (_('Past 5 minutes'), lambda qs, name: qs.filter(**{
            '%s__gte' % name: now() - timedelta(minutes=5),
            '%s__lt' % name: now() + timedelta(minutes=5),
            }))),
        (120, (_('Past hour'), lambda qs, name: qs.filter(**{
            '%s__gte' % name: now() - timedelta(minutes=60),
            '%s__lt' % name: now() + timedelta(minutes=60),
            }))),
        (200, (_('Today'), lambda qs, name: qs.filter(**{
            '%s__year' % name: now().year,
            '%s__month' % name: now().month,
            '%s__day' % name: now().day
        }))),
        (300, (_('Past 24 hours'), lambda qs, name: qs.filter(**{
            '%s__gte' % name: now() - timedelta(days=1),
            '%s__lt' % name: now() + timedelta(days=1),
            }))),
        (400, (_('Past 48 hours'), lambda qs, name: qs.filter(**{
            '%s__gte' % name: now() - timedelta(days=2),
            '%s__lt' % name: now() + timedelta(days=2),
            }))),

        (500, (_('Past 7 days'), lambda qs, name: qs.filter(**{
            '%s__gte' % name: _truncate(now() - timedelta(days=7)),
            '%s__lt' % name: _truncate(now() + timedelta(days=1)),
            }))),
        (600, (_('This month'), lambda qs, name: qs.filter(**{
            '%s__year' % name: now().year,
            '%s__month' % name: now().month
        }))),
        (700, (_('This year'), lambda qs, name: qs.filter(**{
            '%s__year' % name: now().year,
            })))
    ])


class InfoObjectFilter(django_filters.FilterSet):

    # We want to restrict the selection of InfoObject Types to those for which there are actually
    # objects in the system. The first try to do so was the query below, but that becomes awfully
    # slow with many objects in the system, because for some reason, Django makes the sQL query
    # such that it orders as the very first on *all* objects.

    #iobject_type_qs = InfoObjectType.objects.annotate(num_objects=Count('iobject_set')). \
    #    filter(num_objects__gt=0).prefetch_related('iobject_family').order_by('iobject_family__name','name')
  

    # The query below is a lot faster

    iobject_type_qs_a = InfoObject.objects.values('iobject_type__id').distinct()
    iobject_type_qs = InfoObjectType.objects.exclude(iobject_family__name__exact=DINGOS_INTERNAL_IOBJECT_FAMILY_NAME).\
                      filter(pk__in=iobject_type_qs_a.filter()).order_by('iobject_family__name','name').prefetch_related('iobject_family')


    iobject_type =  django_filters.ModelChoiceFilter(queryset= iobject_type_qs,
                                                    required=None,
                                                    label="InfoObject Type",
                                                    to_field_name='id')

    iobject_type__iobject_family = django_filters.ModelChoiceFilter(
        queryset= InfoObjectFamily.objects.exclude(name__exact=DINGOS_INTERNAL_IOBJECT_FAMILY_NAME),
        required=None,
        label="InfoObject Family",
        to_field_name='id')

    identifier__namespace = django_filters.ModelChoiceFilter(
        queryset= IdentifierNameSpace.objects.exclude(uri__exact=DINGOS_ID_NAMESPACE_URI),
        required=None,
        label="ID Namespace",
        to_field_name='id')

    name = django_filters.CharFilter(lookup_type='icontains',
                                                label='Name contains')

    iobject_type__name = django_filters.CharFilter(lookup_type='regex',
                                                label='Object Type matches')

    identifier__uid = django_filters.CharFilter(lookup_type='icontains',
                                                label='ID contains')

    marking_thru__marking__identifier__uid = django_filters.CharFilter(lookup_type='icontains',
                                                                       label='Marking ID contains')

    timestamp = ExtendedDateRangeFilter(label="Object Creation Timestamp")

    create_timestamp = ExtendedDateRangeFilter(label="Import Timestamp")

    class Meta:
        order_by = create_order_keyword_list(['identifier__uid','timestamp','create_timestamp','name','iobject_type','iobject_type__iobject_family'])
        model = InfoObject
        fields = ['iobject_type','iobject_type__name','iobject_type__iobject_family','name',
                  'identifier__namespace','identifier__uid','timestamp', 'create_timestamp','marking_thru__marking__identifier__uid']



class IdSearchFilter(django_filters.FilterSet):

    identifier__namespace = django_filters.ModelChoiceFilter(
        queryset= IdentifierNameSpace.objects.exclude(uri__exact=DINGOS_ID_NAMESPACE_URI),
        required=None,
        label="ID Namespace",
        to_field_name='id')


    identifier__uid = django_filters.CharFilter(lookup_type='icontains',
                                                  label='ID contains')

    class Meta:
	order_by = create_order_keyword_list(['identifier__uid', 'timestamp', 'create_timestamp', 'name', 'iobject_type', 'iobject_type__iobject_family'])
        model = InfoObject
        fields = ['identifier__namespace','identifier__uid']
        #fields = ['iobject_type','iobject_type__iobject_family']


class FactTermValueFilter(django_filters.FilterSet):

    fact__fact_values__value = django_filters.CharFilter(lookup_type='icontains',
                                                         label='Value contains')

    fact__fact_term__term = django_filters.CharFilter(lookup_type='regex',
                                                     label='Fact term matches')

    iobject__name = django_filters.CharFilter(lookup_type='icontains',
                                                     label='Object name contains')



    # We want to restrict the selection of InfoObject Types to those for which there are actually
    # objects in the system. The first try to do so was the query below, but that becomes awfully
    # slow with many objects in the system, because for some reason, Django makes the sQL query
    # such that it orders as the very first on *all* objects.

    #iobject_type_qs = InfoObjectType.objects.annotate(num_objects=Count('iobject_set')). \
    #    filter(num_objects__gt=0).prefetch_related('iobject_family').order_by('iobject_family__name','name')
  
    # The query below is a lot faster


    iobject_type_qs_a = InfoObject.objects.values('iobject_type__id').distinct()
    iobject_type_qs = InfoObjectType.objects.exclude(iobject_family__name__exact=DINGOS_INTERNAL_IOBJECT_FAMILY_NAME).\
                      filter(pk__in=iobject_type_qs_a.all()).order_by('iobject_family__name','name').prefetch_related('iobject_family')


    iobject__iobject_type = django_filters.ModelChoiceFilter(queryset= iobject_type_qs,
                                                required=None,
                                                label="InfoObject Type",
                                                to_field_name='id')



    iobject__timestamp = ExtendedDateRangeFilter(label='Object Timestamp')

    iobject__create_timestamp = ExtendedDateRangeFilter(label='Import Timestamp')

    iobject__timestamp = ExtendedDateRangeFilter(label='Object Timestamp')

    #iobject__iobject_type = django_filters.ModelMultipleChoiceFilter()

    iobject__identifier__namespace = django_filters.ModelChoiceFilter(
        queryset= IdentifierNameSpace.objects.exclude(uri__exact=DINGOS_ID_NAMESPACE_URI),
        required=None,
        label="ID Namespace",
        to_field_name='id')

    iobject__iobject_type__name = django_filters.CharFilter(lookup_type='icontains',
                                                     label='Object Type name contains')



    iobject__marking_thru__marking__identifier__uid = django_filters.CharFilter(lookup_type='icontains',
                                                                       label='Marking ID contains')


    class Meta:
        #order_by = create_order_keyword_list(['iobject__iobject_type__name','iobject__iobject_type','fact__fact_term__term', 'fact__fact_values__value'])
        model = InfoObject2Fact

        fields = ['fact__fact_term__term','fact__fact_values__value','iobject__name','iobject__timestamp','iobject__create_timestamp',
                  'iobject__identifier__namespace','iobject__iobject_type','iobject__iobject_type__name','iobject__marking_thru__marking__identifier__uid']


class OrderedFactTermValueFilter(FactTermValueFilter):

    class Meta:
        order_by = create_order_keyword_list(['iobject__iobject_type__name','iobject__iobject_type','fact__fact_term__term', 'fact__fact_values__value'])
        model = InfoObject2Fact

        fields = ['fact__fact_term__term','fact__fact_values__value','iobject__name','iobject__timestamp','iobject__create_timestamp',
                  'iobject__identifier__namespace','iobject__iobject_type','iobject__iobject_type__name','iobject__marking_thru__marking__identifier__uid']




