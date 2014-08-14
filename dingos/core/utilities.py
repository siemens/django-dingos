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

from django.utils.encoding import smart_text

import re

def listify(x):
    """
    listify(x) returns a singleton list containing x if x is not already a list.
    If x is a list, x itself is returned.

    This function is used when traversing dictionaries created by the DINGO XML
    import: because the XML import knows nothing about the XML schema, it
    cannot know whether a given single element is actually a list of length
    one. For example::

        <foo>
           <bar>1</bar>
        </foo>

    would lead to::

        {'foo' : {'bar' : 1 }}

    whereas::

        <foo>
           <bar>1</bar>
           <bar>2</bar>
        </foo>

    would lead to::

        {'foo' : {'bar' : [1,2]}}

    So when traversing a dictionary structure we might expect a list
    but in case of singletons there will be no list. 'listify' can
    be used instead of case-distinctions.
    """
    if type(x) == type([]):
        return x
    else:
        return [x]


def set_dict(dictionary, value, command='set', *keys):
    """
    set_dict takes a dictionary, the value to
    enter into the dictionary, a command of what
    to do with the value, and a sequence of keys.

    d = {}

    set_dict(d,1,'append','level 1','level 2')

    -> d['level 1']['level 2'] = [1]

    set_dict(d,2,'append','level 1','level 2')

    -> d['level 1']['level 2'] = [1,2]

    """

    existing = dictionary
    for i in range(0, len(keys) - 1):
        if keys[i] in existing:
            existing = existing[keys[i]]
        else:
            existing[keys[i]] = existing.__class__()
            existing = existing[keys[i]]
    if command == 'set':
        existing[keys[len(keys) - 1]] = value
    if command == 'set_value':
        existing[keys[len(keys) - 1]] = {'_value': value}
    elif command == 'append':
        if keys[len(keys) - 1] in existing:
            existing[keys[len(keys) - 1]].append(value)
        else:
            existing[keys[len(keys) - 1]] = [value]
    elif command == 'set_or_append':
        if keys[len(keys) - 1] in existing:
            if type(keys[len(keys) - 1]) == type([]):
                existing[keys[len(keys) - 1]].append(value)
            else:
                existing[keys[len(keys) - 1]] = [existing[keys[len(keys) - 1]], value]
        else:
            existing[keys[len(keys) - 1]] = value
    elif command == 'insert':
        if keys[len(keys) - 1] in existing:
            if not value in existing[keys[len(keys) - 1]]:
                existing[keys[len(keys) - 1]].append(value)
        else:
            existing[keys[len(keys) - 1]] = [value]


def get_dict(dictionary, *keys,**kwargs):
    """
    This function allows traversals over several keys to
    be performed by passing a list of keys::

    get_dict(d,key1,key2,key3) = d[key1][key2][key3]

    """

    if 'default' in kwargs:
        default = kwargs['default']
    else:
        default = None

    existing = dictionary
    for i in range(0, len(keys)):

        if keys[i] in existing:

            existing = existing[keys[i]]
        else:

            return default
    return existing


def search_by_re_list(re_list, text):
    """
    Given a list of compiled regular expressions,
    try to search in text with each matcher until the first
    match occurs. Return the group-dict for that first match.
    """
    for matcher in re_list:
        m = matcher.search(text)
        if m:
            return m.groupdict()
    return None


def get_from_django_obj(obj, fields):
    """
    A function for retrieving values from a django object
    with 'path' generated at runtime. For example, for
    a Dingos 'InfoObject2Fact' object, the following
    will extract the list of values associated with
    the fact referenced in the given InfoObject2Fact
    object::

       get_from_django_obj(iobject_2_fact,['fact','fact_values','value'])

    *Attention*: This function currently just covers
    the cases required for its current usage in Dingos:
    it is likely to mess up in more general cases...
    """
    if not fields:
        return smart_text(obj)
    if 'Manager' in "%s" % obj.__class__:
        return (map(lambda o: get_from_django_obj(o, fields[1:]), obj.all()))
    else:
        #print "Felder"
        #print (fields)
        return get_from_django_obj(getattr(obj, fields[0]), fields[1:])


def replace_by_list(key, replacement_list):
    """
    Replaces all occurences of a regex pattern in the list with its replacement.
    List record format: tuple("<regex_alias>", "<replacement>")
    """
    result = key
    for alias, replacement in replacement_list:
        result = re.sub(alias, replacement, result)

    return result


def is_in_list(value, pattern_list):
    """
    Searches for value in regex list.
    """
    for pattern in pattern_list:
        if re.match(pattern, value):
            return True
    return False


def lookup_in_re_list(re_list, text):
    """
    Given a list of compiled regular expressions paired
    with some other value, try to search in text with each matcher until the first
    match occurs. Return the paired element for the matching matcher.
    """
    for (matcher,elt) in re_list:
        m = matcher.search(text)
        if m:
            return elt
    return None

