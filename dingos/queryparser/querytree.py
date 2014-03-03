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


class Operator:
    OR = "|"
    AND = "&"


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


class FilterCollection:
    def __init__(self):
        self.filter_list = []

    def add_new_filter(self, new_filter):
        self.filter_list.insert(0, new_filter)

    def get_filter_list(self):
        q_list = []
        for i, oneFilter in enumerate(self.filter_list):
            q_list.append(oneFilter.build_q())
        return q_list

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
    def __init__(self, key, comparator, value):
        self.key = key
        self.comparator = comparator
        self.value = value

    def build_q(self):
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

        # Fact term condition
        if self.key[0] == "[" and self.key[-1] == "]":
            key = self.key[1:-1]
            if "@" in key:
                fact_term, fact_attribute = key.split("@")
                result = Q(**{"fact_thru__fact__fact_term__term__iregex": fact_term})
                result = result & Q(**{"fact_thru__fact__fact_term__attribute__iregex": fact_attribute})
            else:
                result = Q(**{"fact_thru__fact__fact_term__term__iregex": key})
            result = result & Q(**{"fact_thru__fact__fact_values__value" + q_operator: self.value})
        # Field condition
        else:
            result = Q(**{self.key + q_operator: self.value})

        return result

    def __repr__(self):
        return "%s %s %s" % (self.key, self.comparator, self.value)
