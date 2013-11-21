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
from dingos.models import InfoObject, InfoObject2Fact, InfoObjectType, InfoObjectFamily,IdentifierNameSpace
from django.db.models import Count

from django.forms.models import ModelChoiceField

from django.utils.translation import ugettext_lazy as _

from datetime import timedelta
from django.utils.timezone import now

_truncate = lambda dt: dt.replace(hour=0, minute=0, second=0)

class ExtendedDateRangeFilter(django_filters.DateRangeFilter):
    options = {
        '': (_('Any date'), lambda qs, name: qs.all()),
        1: (_('Past 5 minutes'), lambda qs, name: qs.filter(**{
            '%s__gte' % name: now() - timedelta(minutes=5),
            '%s__lt' % name: now() + timedelta(minutes=5),
            })),
        2: (_('Today'), lambda qs, name: qs.filter(**{
            '%s__year' % name: now().year,
            '%s__month' % name: now().month,
            '%s__day' % name: now().day
        })),
        3: (_('Past 24 hours'), lambda qs, name: qs.filter(**{
            '%s__gte' % name: now() - timedelta(days=1),
            '%s__lt' % name: now() + timedelta(days=1),
            })),
        4: (_('Past 7 days'), lambda qs, name: qs.filter(**{
            '%s__gte' % name: _truncate(now() - timedelta(days=7)),
            '%s__lt' % name: _truncate(now() + timedelta(days=1)),
            })),
        5: (_('This month'), lambda qs, name: qs.filter(**{
            '%s__year' % name: now().year,
            '%s__month' % name: now().month
        })),
        6: (_('This year'), lambda qs, name: qs.filter(**{
            '%s__year' % name: now().year,
            })),
        }


class InfoObjectFilter(django_filters.FilterSet):


    iobject_type_qs = InfoObjectType.objects.annotate(num_objects=Count('iobject_set')).\
        filter(num_objects__gt=0).prefetch_related('iobject_family').order_by('iobject_family__name','name')

    iobject_type = django_filters.ModelChoiceFilter(queryset= iobject_type_qs,
                                                    required=None,
                                                    label="InfoObject Type",
                                                    to_field_name='id')

    iobject_type__iobject_family = django_filters.ModelChoiceFilter(
                                                    queryset= InfoObjectFamily.objects.all(),
                                                    required=None,
                                                    label="InfoObject Family",
                                                    to_field_name='id')

    identifier__namespace = django_filters.ModelChoiceFilter(
        queryset= IdentifierNameSpace.objects.all(),
        required=None,
        label="ID Namespace",
        to_field_name='id')

    identifier__uid = django_filters.CharFilter(lookup_type='icontains',
                                                label='ID contains')

    timestamp = ExtendedDateRangeFilter(label="Object Timestamp")

    create_timestamp = ExtendedDateRangeFilter(label="Create/Import Timestamp")

    class Meta:
        model = InfoObject
        fields = ['iobject_type','iobject_type__iobject_family',
                  'identifier__namespace','identifier__uid','timestamp', 'create_timestamp']


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

    iobject_type_qs = InfoObjectType.objects.annotate(num_objects=Count('iobject_set')). \
        filter(num_objects__gt=0).prefetch_related('iobject_family').order_by('iobject_family__name','name')

    iobject__iobject_type = django_filters.ModelChoiceFilter(queryset= iobject_type_qs,
                                                required=None,
                                                label="InfoObject Type",
                                                to_field_name='id')

    iobject__timestamp = ExtendedDateRangeFilter(label='Object Timestamp')

    iobject__created_timestamp = ExtendedDateRangeFilter(label='Create/Import Timestamp')

    #iobject__iobject_type = django_filters.ModelMultipleChoiceFilter()

    class Meta:
        model = InfoObject2Fact

        fields = ['fact__fact_term__term','fact__fact_values__value','iobject__timestamp','iobject__created_timestamp',
                  'iobject__identifier__namespace','iobject__iobject_type',]




