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
    def __init__(self):
        self.filter_list = []

    def add_new_filter(self, new_filter):
        self.filter_list.insert(0, new_filter)

    def build_query(self, base=None):
        if not base:
            objects = InfoObject.objects.all()
        else:
            objects = base
        for oneFilter in self.filter_list:
            filter_type = oneFilter['type']
            if filter_type in ['filter', 'exclude']:
                filter_query = oneFilter['expression'].build_q()
                objects = getattr(objects, filter_type)(filter_query)
                print "\t%s: %s" % (filter_type, filter_query)
            elif filter_type in ['marked_by'] and 'negation' in oneFilter:
                print "\t%s:negation=%s {" % (filter_type, oneFilter['negation'])
                q_query = Q(**{'marking_thru__marking__in': oneFilter['query'].build_query()})
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


class Expression:
    def __init__(self, left, operator, right):
        self.left = left
        self.op = operator
        self.right = right

    def build_q(self):
        result = self.left.build_q()
        if self.op == Operator.AND:
            result = result & self.right.build_q()
        elif self.op == Operator.OR:
            result = result | self.right.build_q()
        return result

    def __repr__(self):
        return "(%s %s %s)" % (self.left, self.op, self.right)


class Condition:
    def __init__(self, key, is_not, comparator, value):
        self.key = key
        self.is_not = is_not
        self.comparator = comparator
        self.value = value

    def build_q(self):
        value = self.value

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
            time_val = int(value[:-1])
            get_time_delta= {
                'd': lambda number: timedelta(days=number),
                'h': lambda number: timedelta(hours=number),
                'm': lambda number: timedelta(minutes=number)
            }
            if unit in get_time_delta:
                value = now() - get_time_delta[unit](time_val)
            else:
                raise QueryParserException("Syntax error: Time unit \"%s\" is not supported" % unit)

        if self.key[0] == "[" and self.key[-1] == "]":
            # Fact term condition
            key = self.key[1:-1]
            if "@" in key:
                # Condition for an attribute in the fact term
                fact_term, fact_attribute = key.split("@")
                result = Q(**{"fact_thru__fact__fact_term__term__iregex": fact_term})
                result = result & Q(**{"fact_thru__fact__fact_term__attribute__iregex": fact_attribute})
            else:
                result = Q(**{"fact_thru__fact__fact_term__term__iregex": key})
            result = result & self.enrich_q_with_not(
                Q(**{"fact_thru__fact__fact_values__value" + q_operator: value}))
        else:
            # Field condition
            result = self.enrich_q_with_not(Q(**{self.key + q_operator: value}))

        return result

    def enrich_q_with_not(self, q_object):
        if self.is_not:
            return ~q_object
        return q_object

    def key_is_fact_term(self):
        return self.key[0] == "[" and self.key[-1] == "]"

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
