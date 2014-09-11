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

import re, importlib
from django.db.models import Q
from dingos.models import InfoObject, InfoObject2Fact, Fact
from django.utils import timezone
from django.utils.timezone import now
from django.utils.dateparse import parse_datetime
from datetime import timedelta

from dingos import DINGOS_SEARCH_POSTPROCESSOR_REGISTRY

from dingos.core.utilities import replace_by_list, is_in_list
from dingos import DINGOS_QUERY_ALLOWED_KEYS, DINGOS_QUERY_ALLOWED_COLUMNS



POSTPROCESSOR_REGISTRY = {}


for (postprocessor_key,postprocessor_data) in DINGOS_SEARCH_POSTPROCESSOR_REGISTRY.items():
    my_module = importlib.import_module(postprocessor_data['module'])
    POSTPROCESSOR_REGISTRY[postprocessor_key] = getattr(my_module,postprocessor_data['class'])



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
    LOWEREQUAL = "<="
    LOWERTHAN = "<"
    GREATEREQUAL = ">="
    GREATERTHAN = ">"
    RANGE = "range"
    YOUNGER = "younger"


class FilterCollection:
    INFO_OBJECT = 'InfoObject'
    INFO_OBJECT_2_FACT = 'InfoObject2Fact'

    def __init__(self):
        self.filter_list = []

    def add_new_filter(self, new_filter):
        self.filter_list.insert(0, new_filter)

    def build_query(self, base=None):
        # Do NOT use 'base == None' below: if base is a queryset,
        # this will lead to the query being executed in order to
        # find out whether it delivers no results ...

        if isinstance(base, type(None)):
            objects = InfoObject.objects.all()
        else:
            objects = base

        query_mode = objects.model.__name__

        for oneFilter in self.filter_list:

            filter_type = oneFilter['type']
            negation = oneFilter['negation']
            expr_or_query = oneFilter['expr_or_query']

            if filter_type in ['object']:
                expression_repr = expr_or_query
                q_obj = expression_repr.build_q_obj(query_mode=query_mode, filter_type=filter_type)
                if negation:
                    objects = getattr(objects, 'exclude')(q_obj)
                else:
                    objects = getattr(objects, 'filter')(q_obj)
                #print "\t%s (negated: %s): %s" % (filter_type,negation,q_obj)

            elif filter_type in ['fact']:
                expression_repr = expr_or_query
                #print expression_repr
                #print expression_repr.__class__
                fact_q_obj = expression_repr.build_q_obj(query_mode=self.INFO_OBJECT, filter_type=filter_type)
                if query_mode == self.INFO_OBJECT:
                    q_key = 'facts__in'
                elif query_mode == self.INFO_OBJECT_2_FACT:
                    q_key = 'fact__in'
                #print "Expression %s %s" % (expression_repr, fact_q_obj)
                sub_query = Fact.objects.filter(fact_q_obj)
                q_obj = Q(**{q_key: sub_query})
                if negation:
                    objects = getattr(objects, 'exclude')(q_obj)
                else:
                    objects = getattr(objects, 'filter')(q_obj)

            elif filter_type in ['marked_by']:
                query_repr = expr_or_query

                #print "\t%s: negation=%s {" % (filter_type, negation)
                sub_query = query_repr.build_query(base=InfoObject.objects.all())

                q_key = ''
                if query_mode == self.INFO_OBJECT_2_FACT:
                    q_key += 'iobject__'
                q_key += 'marking_thru__marking__in'
                q_obj = Q(**{q_key: sub_query})
                if negation:
                    objects = getattr(objects, 'exclude')(q_obj)
                else:
                    objects = getattr(objects, 'filter')(q_obj)
                #print "\t}"

        return objects

    def __repr__(self):
        result = "{"
        for i, cur in enumerate(self.filter_list):
            if i != 0:
                result += " --> "
            result += str(cur)
        result += "}"
        return result


class ReferencedByFilterCollection:
    def __init__(self, formatted_filter_collection, refby_filter_collection = None, refby_filter_args = []):
        self.formatted_filter_collection = formatted_filter_collection
        self.refby_filter_collection = refby_filter_collection

        self.refby_filter_args = {}
        for arg in refby_filter_args:
            arg_value = arg['value'][1:-1]
            if re.match('true', arg_value, flags=re.IGNORECASE):
                self.refby_filter_args[arg['key']] = True
            elif re.match('false', arg_value, flags=re.IGNORECASE):
                self.refby_filter_args[arg['key']] = False
            elif re.match('\d+', arg_value):
                self.refby_filter_args[arg['key']] = int(arg_value)
            else:
                self.refby_filter_args[arg['key']] = arg_value


class FormattedFilterCollection:
    def __init__(self, filter_collection, format_args=[], output_format='default'):
        self.filter_collection = filter_collection
        self.format = output_format
        self.format_args = format_args

    def build_format_arguments(self,query_mode=FilterCollection.INFO_OBJECT):

        if self.format == 'default':
            return {'columns': {'headers':[],'selected_fields':[]},
                    'kwargs': {},
                    'prefetch_related':[],
                    'postprocessor' : None}

        if self.format in POSTPROCESSOR_REGISTRY:
            postprocessor_class = POSTPROCESSOR_REGISTRY[self.format]
            postprocessor = postprocessor_class(query_mode=query_mode)
            allowed_columns = postprocessor.allowed_columns
            if postprocessor.query_mode_restriction and not query_mode in postprocessor.query_mode_restriction:
                raise QueryParserException("Postprocessor %s cannot be used for %s queries" % (self.format,query_mode))
        else:
            raise QueryParserException("Unknown postprocessor %s" % (self.format))



        # Split format_args into col_specs and misc_args (contains additional output configuration)
        col_specs = []
        misc_args = {}
        if self.format_args:
            for format_arg in self.format_args:
                if type(format_arg) is dict:
                    misc_args[format_arg['key']] = format_arg['value']
                else:
                    col_specs.append(format_arg)

        # Reformat structure of column specifications
        prefetch_related_fields = set()

        split = {'headers': [], 'selected_fields': []}
        if len(col_specs) is not 0:

            header = None
            for spec in col_specs:
                if ':' in spec:
                    # Use user-defined header
                    (header, selected_field) = spec.split(':')
                    header = header.strip()
                    selected_field = selected_field.strip()
                else:

                    selected_field = spec




                if not selected_field in postprocessor.allowed_columns.keys():
                    raise QueryParserException("Column \"" + selected_field + "\" is not allowed; "
                                                                              "please restrict yourself to the "
                                                                              "following columns: %s" %
                                               ", ".join(sorted(postprocessor.allowed_columns.keys())))
                for prefetch in postprocessor.allowed_columns[selected_field][2]:
                    prefetch_related_fields.add(prefetch)
                if not header:
                    header = postprocessor.allowed_columns[selected_field][0]

                split['headers'].append(header)

                split['selected_fields'].append(selected_field)

        else:
            for i in postprocessor.default_columns:
                split['headers'].append(i[1])
                split['selected_fields'].append(i[0])
                for prefetch in postprocessor.allowed_columns[i[0]][2]:
                    prefetch_related_fields.add(prefetch)


        col_specs = split
        result = {'columns':col_specs,
                'kwargs':misc_args,
                'prefetch_related':list(prefetch_related_fields),
                'postprocessor' : postprocessor}

        print result
        return result

class Expression:
    def __init__(self, left, operator, right):
        self.left = left
        self.op = operator
        self.right = right

    def build_q_obj(self, query_mode=FilterCollection.INFO_OBJECT, filter_type='object'):
        result = self.left.build_q_obj(query_mode=query_mode, filter_type=filter_type)
        if self.op == Operator.AND:
            result = result & self.right.build_q_obj(query_mode=query_mode, filter_type=filter_type)
        elif self.op == Operator.OR:
            result = result | self.right.build_q_obj(query_mode=query_mode, filter_type=filter_type)
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

    def build_q_obj(self, query_mode=FilterCollection.INFO_OBJECT, filter_type='object'):
        value = self.value
        if not is_in_list(self.key, map(lambda x: x[0],DINGOS_QUERY_ALLOWED_KEYS[filter_type])):
            raise QueryParserException("Key \"" + self.key + "\" is not allowed; please restrict yourself to keys of the following form: %s" % ", ".join(map( lambda x : x[0].replace('\\','').replace('^','').replace('$',''),DINGOS_QUERY_ALLOWED_KEYS[filter_type])))

        if not self.key[0] in ['[','@']:
            key = replace_by_list(self.key, DINGOS_QUERY_ALLOWED_KEYS[filter_type])
        else:
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
        elif self.comparator == Comparator.LOWEREQUAL:
            q_operator = "__lte"
            # Value format:
            # YYYY-mm-dd
            value = generate_date_value(value + " 23:59:59")
        elif self.comparator == Comparator.LOWERTHAN:
            q_operator = "__lt"
            # Value format:
            # YYYY-mm-dd
            value = generate_date_value(value + " 00:00:00")
        elif self.comparator == Comparator.GREATEREQUAL:
            q_operator = "__gte"
            # Value format:
            # YYYY-mm-dd
            value = generate_date_value(value + " 00:00:00")
        elif self.comparator == Comparator.GREATERTHAN:
            q_operator = "__gt"
            # Value format:
            # YYYY-mm-dd
            value = generate_date_value(value + " 23:59:59")
        elif self.comparator == Comparator.RANGE:
            q_operator = "__range"
            # Value format:
            # YYYY:mm:dd HH:MM:SS -- YYYY:mm:dd HH:MM:SS
            (begin_value, end_value) = value.split("--")
            begin = generate_date_value(begin_value.strip())
            end = generate_date_value(end_value.strip())
            value = (begin, end)
        elif self.comparator == Comparator.YOUNGER:
            q_operator = "__gt"
            # Value example: timestamp younger '4d'
            unit = value[-1].lower()
            try:
                time_val = int(value[:-1])
            except ValueError:
                raise QueryParserException("Syntax error: Time span has to be in the format of \"[0-9]+[dhmDHM]\".")
            get_time_delta = {
                'd': lambda number: timedelta(days=number),
                'h': lambda number: timedelta(hours=number),
                'm': lambda number: timedelta(minutes=number)
            }
            if unit in get_time_delta:
                value = now() - get_time_delta[unit](time_val)
            else:
                raise QueryParserException(
                    "Syntax error: Time unit \"%s\" is not supported. Supported time units are %s."
                    % (unit, ", ".join(get_time_delta.keys())))

        # Query
        q_query_prefix = ""

        if key[0] == '@' and key[1] == '[' and key[-1] == ']':
            #if filter_type != 'fact':
            #    raise QueryParserException("@[attribute] <op> <value> shortcut is only allowed in fact-filters")
            key = key[2:-1]
            sub_q_obj = Q(**{"fact_term__attribute__iregex": key})
            sub_q_obj = sub_q_obj & self.enrich_q_with_not(Q(**{"fact_values__value" + q_operator: value}))
            return Q(iobject_thru__attributes__fact__in=Fact.objects.filter(sub_q_obj))

        if key[0] == "[" and key[-1] == "]":
            #if filter_type != 'fact':
            #    raise QueryParserException("[term] <op> <value> shortcut is only allowed in fact-filters")

            #if query_mode == FilterCollection.INFO_OBJECT:
            #    q_query_prefix = "fact_thru__"

            # Fact term condition
            key = key[1:-1]
            if "@" in key:
                # Condition for an attribute in the fact term
                fact_term, fact_attribute = key.split("@")
                result = Q(**{q_query_prefix + "fact_term__term__iregex": fact_term})
                result = result & Q(**{q_query_prefix + "fact_term__attribute__iregex": fact_attribute})
            else:
                result = Q(**{q_query_prefix + "fact_term__term__iregex": key})
            result = result & self.enrich_q_with_not(
                Q(**{q_query_prefix + "fact_values__value" + q_operator: value}))
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

