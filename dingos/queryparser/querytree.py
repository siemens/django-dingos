# Copyright (c) Siemens AG, 2014
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
from django.db.models import Q
from dingos.models import InfoObject
from django.utils import timezone
from django.utils.timezone import now
from django.utils.dateparse import parse_datetime
from datetime import timedelta


class QueryParserException(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg


class Operator:
    OR = "||"
    AND = "&&"


class Comparator:
    EQUALS = "="
    CONTAINS = "contains"
    ICONTAINS = "icontains"
    REGEXP = "regexp"
    IREGEXP = "iregexp"
    STARTSWITH = "startswith"
    ISTARTSWITH = "istartswith"
    ENDSWITH = "endswith"
    IENDSWITH = "iendswith"
    LOWERTHAN = "<"
    RANGE = "range"
    YOUNGER = "younger"


class FilterCollection:
    INFO_OBJECT = "InfoObject"
    INFO_OBJECT_2_FACT = "InfoObject2Fact"

    def __init__(self):
        self.filter_list = []

    def add_new_filter(self, new_filter):
        self.filter_list.insert(0, new_filter)

    def build_query(self, base=None, query_mode=None):
        # Do NOT use 'base == None' below: if base is a queryset,
        # this will lead to the query being executed in order to
        # find out whether it delivers no results ...

        if isinstance(base,type(None)):
            objects = InfoObject.objects.all()
        else:
            objects = base
        for oneFilter in self.filter_list:
            filter_type = oneFilter['type']
            if filter_type in ['filter', 'exclude']:
                filter_query = oneFilter['expression'].build_q(query_mode)
                objects = getattr(objects, filter_type)(filter_query)
                print "\t%s: %s" % (filter_type, filter_query)
            elif filter_type in ['marked_by'] and 'negation' in oneFilter:
                print "\t%s: negation=%s {" % (filter_type, oneFilter['negation'])
                q_key = ''
                if query_mode == self.INFO_OBJECT_2_FACT:
                    q_key += 'iobject__'
                q_key += 'marking_thru__marking__in'
                q_query = Q(**{q_key: oneFilter['query'].build_query(query_mode=self.INFO_OBJECT)})
                if oneFilter['negation']:
                    objects = getattr(objects, 'exclude')(q_query)
                else:
                    objects = getattr(objects, 'filter')(q_query)
                print "\t}"

        return objects

    def __repr__(self):
        result = "{"
        for i, cur in enumerate(self.filter_list):
            if i != 0:
                result += " --> "
            result += str(cur)
        result += "}"
        return result


class FormattedFilterCollection:
    def __init__(self, filter_collection, format_args=[], format='default'):
        self.filter_collection = filter_collection
        self.format = format

        # Split format_args into col_specs and misc_args (contains additional output configuration)
        col_specs = []
        misc_args = {}
        for format_arg in format_args:
            if type(format_arg) is dict:
                misc_args[format_arg['key']] = format_arg['value']
            else:
                col_specs.append(format_arg)
        self.misc_args = misc_args

        # Reformat structure of column specifications
        split = {'headers': [], 'selected_fields': []}
        if len(col_specs) is not 0:
            (split['headers'], split['selected_fields']) = zip(*(spec.split(':') for spec in col_specs))
        self.col_specs = split


class Expression:
    def __init__(self, left, operator, right):
        self.left = left
        self.op = operator
        self.right = right

    def build_q(self, query_mode=FilterCollection.INFO_OBJECT):
        result = self.left.build_q(query_mode)
        if self.op == Operator.AND:
            result = result & self.right.build_q(query_mode)
        elif self.op == Operator.OR:
            result = result | self.right.build_q(query_mode)
        return result

    def __repr__(self):
        return "(%s %s %s)" % (self.left, self.op, self.right)


class Condition:
    def __init__(self, key, is_not, comparator, value):
        # Replace query language hierarchy separator with python-ish syntax
        self.key = key
        self.is_not = is_not
        self.comparator = comparator
        self.value = value

    def build_q(self, query_mode=FilterCollection.INFO_OBJECT):
        value = self.value
        key = self.key

        # Operator choice
        q_operator = ""
        if self.comparator == Comparator.EQUALS:
            q_operator = "__iexact"
        elif self.comparator == Comparator.CONTAINS:
            q_operator = "__contains"
        elif self.comparator == Comparator.ICONTAINS:
            q_operator = "__icontains"
        elif self.comparator == Comparator.REGEXP:
            q_operator = "__regex"
        elif self.comparator == Comparator.IREGEXP:
            q_operator = "__iregex"
        elif self.comparator == Comparator.STARTSWITH:
            q_operator = "__startswith"
        elif self.comparator == Comparator.ISTARTSWITH:
            q_operator = "__istartswith"
        elif self.comparator == Comparator.ENDSWITH:
            q_operator = "__endswith"
        elif self.comparator == Comparator.IENDSWITH:
            q_operator = "__iendswith"
        elif self.comparator == Comparator.LOWERTHAN:
            q_operator = "__lt"
            # Value format:
            # YYYY:mm:dd
            value = generate_date_value(value + " 00:00:00")
        elif self.comparator == Comparator.RANGE:
            q_operator = "__range"
            # Value format:
            # YYYY:mm:dd HH:MM:SS -- YYYY:mm:dd HH:MM:SS
            (beginValue, endValue) = value.split("--")
            begin = generate_date_value(beginValue.strip())
            end = generate_date_value(endValue.strip())
            value = (begin, end)
        elif self.comparator == Comparator.YOUNGER:
            q_operator = "__gt"
            # Value example: timestamp younger '4d'
            unit = value[-1].lower()
            try:
                time_val = int(value[:-1])
            except ValueError as ex:
                raise QueryParserException("Syntax error: Time span has to be in the format of \"[0-9]+[dhmDHM]\".")
            get_time_delta = {
                'd': lambda number: timedelta(days=number),
                'h': lambda number: timedelta(hours=number),
                'm': lambda number: timedelta(minutes=number)
            }
            if unit in get_time_delta:
                value = now() - get_time_delta[unit](time_val)
            else:
                raise QueryParserException("Syntax error: Time unit \"%s\" is not supported. Supported time units are %s." % (unit, ", ".join(get_time_delta.keys())))

        # Query
        q_query_prefix = ""
        if key[0] == "[" and key[-1] == "]":
            if query_mode == FilterCollection.INFO_OBJECT:
                q_query_prefix = "fact_thru__"

            # Fact term condition
            key = key[1:-1]
            if "@" in key:
                # Condition for an attribute in the fact term
                fact_term, fact_attribute = key.split("@")
                result = Q(**{q_query_prefix + "fact__fact_term__term__iregex": fact_term})
                result = result & Q(**{q_query_prefix + "fact__fact_term__attribute__iregex": fact_attribute})
            else:
                result = Q(**{q_query_prefix + "fact__fact_term__term__iregex": key})
            result = result & self.enrich_q_with_not(Q(**{q_query_prefix + "fact__fact_values__value" + q_operator: value}))
        else:
            # Field condition
            key = key.replace(".", "__")
            if query_mode == FilterCollection.INFO_OBJECT_2_FACT:
                q_query_prefix = "iobject__"
            key = q_query_prefix + key
            result = self.enrich_q_with_not(Q(**{key + q_operator: value}))

        return result

    def enrich_q_with_not(self, q_object):
        if self.is_not:
            return ~q_object
        return q_object

    def __repr__(self):
        return "%s %s %s" % (self.key, self.comparator, self.value)


def generate_date_value(old_value):
    naive = parse_datetime(old_value.strip())
    if naive:
        # Make sure that information regarding the timezone is
        # included in the time stamp. If it is not, we choose
        # UTC as default timezone.
        if not timezone.is_aware(naive):
            return timezone.make_aware(naive, timezone.utc)
        else:
            return naive
    else:
        raise QueryParserException("Syntax error: Cannot read date \"%s\"" % old_value)
