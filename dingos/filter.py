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
from dingos.models import InfoObject, InfoObject2Fact, InfoObjectType
from django.db.models import Count

from django.forms.models import ModelChoiceField

from django.utils.translation import ugettext_lazy as _

from datetime import timedelta
from django.utils.timezone import now

_truncate = lambda dt: dt.replace(hour=0, minute=0, second=0)

class ExtendedDateRangeFilter(django_filters.DateRangeFilter):
    options = {
        '': (_('Any date'), lambda qs, name: qs.all()),
        1: (_('Today'), lambda qs, name: qs.filter(**{
            '%s__year' % name: now().year,
            '%s__month' % name: now().month,
            '%s__day' % name: now().day
        })),
        2: (_('Past 24 hours'), lambda qs, name: qs.filter(**{
            '%s__gte' % name: now() - timedelta(days=1),
            '%s__lt' % name: now() + timedelta(days=1),
            })),
        3: (_('Past 7 days'), lambda qs, name: qs.filter(**{
            '%s__gte' % name: _truncate(now() - timedelta(days=7)),
            '%s__lt' % name: _truncate(now() + timedelta(days=1)),
            })),
        4: (_('This month'), lambda qs, name: qs.filter(**{
            '%s__year' % name: now().year,
            '%s__month' % name: now().month
        })),
        5: (_('This year'), lambda qs, name: qs.filter(**{
            '%s__year' % name: now().year,
            })),
        }


class InfoObjectFilter(django_filters.FilterSet):

    identifier__uid = django_filters.CharFilter(lookup_type='icontains',
                                                label='ID contains')


    iobject_type_qs = InfoObjectType.objects.annotate(num_objects=Count('infoobject')).\
        filter(num_objects__gt=0).prefetch_related('iobject_family').order_by('iobject_family__name','name')

    iobject_type = django_filters.ModelChoiceFilter(queryset= iobject_type_qs,
                                                    required=None,
                                                    label="InfoObject Type",
                                                    to_field_name='id')
    timestamp = ExtendedDateRangeFilter()

    class Meta:
        model = InfoObject
        fields = ['iobject_type','iobject_type__iobject_family','identifier__namespace','identifier__uid','timestamp']

class InfoObjectEmbeddedFilter(django_filters.FilterSet):

    iobject__identifier__uid = django_filters.CharFilter(lookup_type='icontains',
                                                label='ID contains')

    iobject__timestamp = ExtendedDateRangeFilter()

    class Meta:
        model = InfoObject2Fact
        fields = ['iobject__iobject_type','iobject__iobject_type__iobject_family','iobject__identifier__namespace','iobject__identifier__uid','iobject__timestamp']


class IdSearchFilter(django_filters.FilterSet):

    identifier__uid = django_filters.CharFilter(lookup_type='icontains',
                                                  label='ID contains')



    class Meta:
        model = InfoObject
        fields = ['identifier__namespace','identifier__uid']
        #fields = ['iobject_type','iobject_type__iobject_family']


class FactTermValueFilter(django_filters.FilterSet):

    fact__fact_values__value = django_filters.CharFilter(lookup_type='icontains',
                                                         label='Value contains')

    fact__fact_term__term = django_filters.CharFilter(lookup_type='icontains',
                                                     label='Fact term contains')

    iobject__timestamp = ExtendedDateRangeFilter()

    #iobject__iobject_type = django_filters.ModelMultipleChoiceFilter()

    class Meta:
        model = InfoObject2Fact

        fields = ['fact__fact_term__term','fact__fact_values__value','iobject__timestamp','iobject__identifier__namespace','iobject__iobject_type',]




