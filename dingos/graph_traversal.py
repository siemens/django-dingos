# Copyright (c) Siemens AG, 2014
#
# This file is part of MANTIS.  MANTIS is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
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

from django.db.models import Count, F, Q

from dingos.models import InfoObject2Fact, InfoObject


def find_ancestors(iobject_pks,ancestor_iobject_identifier_pks=None,skip_terms=None):

    if not ancestor_iobject_identifier_pks:
        ancestor_iobject_identifier_pks = []

    if skip_terms==None:
        skip_terms = {'term':'related',
                      'operator':'icontains'}


        Q_skip_terms = Q(facts__fact_term__term__icontains='adfasdfasdf')

    ancestors = InfoObject. \
        objects.exclude(identifier_id__in=ancestor_iobject_identifier_pks). \
        filter(~Q_skip_terms &
               (Q(facts__value_iobject_id__latest__in=iobject_pks,
                  facts__value_iobject_ts=None)
               )
    ).prefetch_related('identifier')

    ancestor_info = map(lambda x: (x.pk,x.identifier.pk), ancestors)

    print "Ancestors: %s" % ancestor_info

    #ancestor_list = list(ancestors.values_list('identifier__id',flat=True))

    ancestor_identifiers = map(lambda x : x[1],ancestor_info)

    ancestor_objects = map(lambda x : x[0],ancestor_info)

    print "Ancestor Ids %s" % ancestor_identifiers

    if ancestor_info == []:
        return ancestor_iobject_identifier_pks
    else:
        return find_ancestors(ancestor_objects, ancestor_iobject_identifier_pks=ancestor_iobject_identifier_pks+ancestor_identifiers)

def find_descendants(iobject_pks,
                     descendant_iobject_pks=None,
                     skip_terms=None):

    if not descendant_iobject_pks:
        descendant_iobject_pks = set()

    if skip_terms==None:
        skip_terms = {'term':'related',
                      'operator':'icontains'}

        Q_skip_terms = Q(fact__fact_term__term__icontains='adfasdfasdf')

    #def find_descendants_rec(iobject_pks):

    children_wo_timestamp_iobject_pks = InfoObject2Fact. \
        objects.filter(iobject_id__in=iobject_pks). \
        filter(~(Q_skip_terms | Q(fact__value_iobject_id=None)) &
               Q(fact__value_iobject_ts=None)). \
        prefetch_related('iobject__identifier'). \
        values_list('fact__value_iobject_id__latest__pk',flat=True)

    children_wo_timestamp_iobject_pks = set(children_wo_timestamp_iobject_pks)

    if children_wo_timestamp_iobject_pks.issubset(descendant_iobject_pks):
        return descendant_iobject_pks
    else:
        return find_descendants(children_wo_timestamp_iobject_pks - descendant_iobject_pks, descendant_iobject_pks=descendant_iobject_pks | children_wo_timestamp_iobject_pks)


