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


def get_dict(dictionary, *keys):
    """
    This function allows traversals over several keys to
    be performed by passing a list of keys::

    get_dict(d,key1,key2,key3) = d[key1][key2][key3]

    """

    existing = dictionary
    for i in range(0, len(keys)):
        if keys[i] in existing:
            existing = existing[keys[i]]
        else:
            return None
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
