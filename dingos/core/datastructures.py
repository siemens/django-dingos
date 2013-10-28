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



import logging
import re

from django.utils.datastructures import SortedDict

logger = logging.getLogger(__name__)



def dict2tuple(mydict):
    """
    Turn a dictionary of the form used by DINGO
    (i.e., a key is mapped to either another dictionary,
    a list or a value) into a tuple-representation.
    This is useful for providing a standard python object that
    observes the order of elements (which standard dictionaries don't).
    """
    result = []
    for key in mydict.keys():
        # There are three cases we need to consider:
        # dictionary, list, and other values
        try:
            # We test whether the object is a dictionary-like
            # structure via accessing the
            keys = mydict[key].keys()
            key_result = dict2tuple(mydict[key])
        except AttributeError:
            # So we have either a list or a value
            if type(mydict[key]) == type([]):
                key_result = []
                for elt in mydict[key]:
                    key_result.append(dict2tuple(elt))
            else:
                key_result = mydict[key]
        result.append((key, key_result))
    return tuple(result)


def tuple2dict(mytuple, constructor=dict):
    """
    Turn a tuple as returned by dict2tuple back
    into a dictionary structure. The optional
    parameter "constructor" governs, what class
    is used to create the dictionary: by default,
    the standard dict class is used, but in DINGO
    we mostly use the DingoObjDict class.
    """
    result = constructor()
    for elt in mytuple:
        key, value = elt
        if type(value) == type(()):
            key_value = tuple2dict(value, constructor=constructor)
        elif type(value) == type([]):
            key_value = []
            for elt in value:
                key_value.append(tuple2dict(elt, constructor=constructor))
        else:
            key_value = value
        result[key] = key_value
    return result


class ExtendedSortedDict(SortedDict):
    """
    ExtendedSortedDict adds a few convenient
    methods to Django's SortedDict class.
    """
    #def copy(self):
    #    obj = self.__class__(self)
    #    obj.keyOrder = self.keyOrder[:]
    #    return obj

    def to_tuple(self):
        """
        Turn an extended sorted dictionary of the form used by DINGO
        (i.e., a key is mapped to either another dictionary,
        a list or a value) into a tuple-representation.
        This is useful for providing a standard python object that
        observes the order of elements (which standard dictionaries don't).

        """
        return dict2tuple(self)

    def to_dict(self):
        """
        Turn an extended sorted dictionary of the form used by DINGO
        (i.e., a key is mapped to either another dictionary,
        a list or a value) into a normal dictionary (i.e., the
        key order is lost).
        """
        return tuple2dict(dict2tuple(self))


    def chained_get(self, *keys):
        """
        This function allows traversals over several keys to
        be performed by passing a list of keys::

            d.chained_get(key1,key2,key3) = d[key1][key2][key3]

        """
        existing = self
        for i in range(0, len(keys)):
            if keys[i] in existing:
                existing = existing[keys[i]]
            else:
                return None
        return existing

    def chained_set(self, value, command='set', *keys):
        """
        chained_set takes the value to
        enter into the dictionary, a command of what
        to do with the value, and a sequence of keys.

        Examples:

        d = {}

        d.chained_set(1,'append','level 1','level 2')

        -> d['level 1']['level 2'] = [1]

        d.chained_set(2,'append','level 1','level 2')

        -> d['level 1']['level 2'] = [1,2]

        """
        new_object = self.__class__()
        existing = self
        for i in range(0, len(keys) - 1):
            if keys[i] in existing:
                existing = existing[keys[i]]
            else:
                existing[keys[i]] = new_object
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


class DingoObjDict(ExtendedSortedDict):
    """
    The DingoObjDict extends the ExtendedSortedDict with
    a flatten function that flattens out the dictionary
    into a list of facts. For details, see below in the
    documentation of the flatten function.
    """

    # TODO Remove commented-out code
    #def dictify(self):
    #   return dict([(k, (v.dictify() if isinstance(v,dict) else v))
    #                  for (k,v) in self.items()])

    #def __repr__(self):
    #
    #    old_dict = self.dictify()
    #    return old_dict.__repr__()



    def flatten(self, attr_ignore_predicate=None):
        """
        Flatten a Dingo dictionary representation of into a list
        of fact-term/value pairs and associated information about tree structure (in node_id)
        and a dictionary mapping XML attributes to node identifiers.

        This all is best explained by example (see below).

        Note that attributes are also represented in the flattened representation. There
        are cases in which attributes should not lead to an entry in the flattened representation.
        This can be configured by passing the flatten method a predicate function 'attr_ignore_predicate'.
        The function takes a dictionary and returns True (ignore) or False (do not ignore). It
        is passed the dictionary representing an entry in the flat representation, such as follows::

              { 'node_id': 'N001:L000:N000:A000',
              'term': 'Hashes/Hash/Simple_Hash_Value',
              'attribute': 'condition',
              'value': u'Equals'},

        By default, the following predicate is used::

             (lambda x : '@' in x['attribute'])

        This is because during import, DINGO adds certain annotations to the import dictionary
        as attributes with a second leading '@'.

        Input Example (CybOx)::

            {'File_Name': {'@condition': 'Equals',  '_value': u'UNITED NATIONS COMPENSATION SCHEME...pdf'},
              'Hashes': {'Hash': [{'Simple_Hash_Value':
                                    {'@condition': 'Equals',
                                     '@datatype': 'hexBinary',
                                      '_value': u'576fea79dd23a352a14c3f8bf3dbc9eb732e1d54f804a29160894aec55df4bd5'},
                                   'Type': {'_value': 'SHA256'}},
                                  {'Simple_Hash_Value': {'@condition': 'Equals',
                                                         '@datatype': 'hexBinary',
                                                         '_value': u'491809c2092cecd633e43d465409a78c'},
                                   'Type': {'_value': 'MD5'}}]
                        }
            }

        Output Example::

          [ { 'node_id': 'N000',
              'term': 'File_Name',
              'attribute': False,
              'value': u'UNITED NATIONS COMPENSATION SCHEME...pdf'},
              { 'node_id': 'N000:A000',
              'term': 'File_Name',
              'attribute': 'condition',
              'value': u'Equals'},
            { 'node_id': 'N001:L000:N000',
              'term': 'Hashes/Hash/Simple_Hash_Value',
              'attribute': False,
              'value': u'576fea79dd23a352a14c3f8bf3dbc9eb732e1d54f804a29160894aec55df4bd5'},
            { 'node_id': 'N001:L000:N000:A000',
              'term': 'Hashes/Hash/Simple_Hash_Value',
              'attribute': 'condition',
              'value': u'Equals'},
            { 'node_id': 'N001:L000:N000:A001',
              'term': 'Hashes/Hash/Simple_Hash_Value',
              'attribute': 'datatype',
              'value': u'hexBinary'},
            { 'node_id': 'N001:L000:N001',
              'term': 'Hashes/Hash/Type',
              'attribute': False,
              'value': 'SHA256'},
            { 'node_id': 'N001:L001:N000',
              'term': 'Hashes/Hash/Simple_Hash_Value',
              'attribute': False,
              'value': u'491809c2092cecd633e43d465409a78c'},
            { 'node_id': 'N001:L001:N000:A000',
              'term': 'Hashes/Hash/Simple_Hash_Value',
              'attribute': 'condition',
              'value': u'Equals'},
            { 'node_id': 'N001:L001:N000:A001',
              'term': 'Hashes/Hash/Simple_Hash_Value',
              'attribute': 'datatype',
              'value': u'hexBinary'},
            { 'node_id': 'N001:L001:N001',
              'term': 'Hashes/Hash/Type',
              'attribute': False,
              'value': 'MD5'}
          ]

          { 'N000': { 'condition': 'Equals'},
            'N001:L000:N000': { 'condition': 'Equals', 'datatype': 'hexBinary'},
            'N001:L001:N000': { 'condition': 'Equals', 'datatype': 'hexBinary'},
          }

        """
        return self._flatten(result_list=[], attr_dict={}, namespace=[], prefix=[],
                             attr_ignore_predicate=attr_ignore_predicate)


    def _flatten(self, result_list, attr_dict, namespace, prefix, attr_ignore_predicate=None):
        """
        Flatten a Dingo dictionary representation of an infomration object into a list
        of fact-term/value pairs and associated information about tree structure (in node_id)
        and XML attributes.

        Internal function for recursive calls.

        """

        def node_id_gen(n):
            """
            Given an integer, generate a fixed-length representation.

            This is used for coding tree-node representations such
            as N001:N005:N009 (9th child of 5th child of 1st child).

            Currently, we use three digits, i.e., we get problems
            if we import stuff with more than 1000 children in a node.

            """

            return "%s%03d" % (n[0], n[1])

        if not attr_ignore_predicate:
            attr_ignore_predicate = (lambda x: '@' in x['attribute'])

        RE_ELEMENT_MATCHER = re.compile(r"[^@_].*")

        attributes = filter(lambda x: x[0] == '@', self.keys())

        node_id = ':'.join(map(node_id_gen, prefix))
        for attribute in attributes:
            if node_id not in attr_dict.keys():
                attr_dict[node_id] = {attribute[1:]: self[attribute]}
            else:
                attr_dict[node_id][attribute[1:]] = self[attribute]

        elements = filter(lambda x: RE_ELEMENT_MATCHER.match(x), self)

        if elements == []:
            logger.debug("Entered _VALUE branch for %s" % self)
            if '_value' in self.keys() or attributes != []:
                result_list.append({'term': '/'.join(namespace),
                                    'value': self.get('_value', ''),
                                    'attribute': False,
                                    'node_id': node_id})

        else:

            counter = 0
            for element in elements:
                logger.debug("Processing element %s" % element)
                if type(self[element]) == type([]):
                    logger.debug("Entered list branch for %s " % self[element])
                    for sub_elt in self[element]:
                        (result_list, attr_dict) = sub_elt._flatten(result_list=result_list,
                                                                    attr_dict=attr_dict,
                                                                    namespace=namespace + [element],
                                                                    prefix=prefix + [('L', counter)],
                                                                    attr_ignore_predicate=attr_ignore_predicate
                        )
                        counter += 1
                elif type(self[element]) == type("hallo") or type(self[element]) == unicode:
                    logger.debug("Entered value branch for %s" % self[element])
                    # added this branch to deal with abbreviated dictionaries
                    # that provide value direcly rather then via '_value' key in dictionary

                    # temporarily append namespace
                    namespace.append(element)

                    fact_data = {'term': '/'.join(namespace),
                                 'value': self[element],
                                 'attribute': False,
                                 'node_id': "%s" % ':'.join(map(node_id_gen, prefix + [('N', counter)]))}
                    result_list.append(fact_data)
                    # clean up namespace
                    namespace = namespace[:-1]
                    counter += 1
                else:
                    logger.debug("Recursing for %s" % self[element])
                    (result_list, attr_dict) = self[element]._flatten(result_list=result_list,
                                                                      attr_dict=attr_dict,
                                                                      namespace=namespace + [element],
                                                                      prefix=prefix + [('N', counter)],
                                                                      attr_ignore_predicate=attr_ignore_predicate)
                    counter += 1

        attr_counter = 0
        for attribute in attributes:
            if node_id == '':
                attr_node_id = node_id_gen(('A', attr_counter))
            else:
                attr_node_id = "%s:%s" % (node_id, node_id_gen(('A', attr_counter)))
            fact = {'term': "%s" % ('/'.join(namespace)),
                    'value': self[attribute],
                    'node_id': attr_node_id,
                    'attribute': attribute[1:]}
            if not attr_ignore_predicate(fact):
                result_list.append(fact)
                attr_counter += 1

        result_list.sort(key=lambda x: x['node_id'])

        return (result_list, attr_dict)


def dict2DingoObjDict(data):
    """
    Turn a dictionary of the form used by DINGO
    (i.e., a key is mapped to either another dictionary,
    a list or a value) into a DingoObjDict.
    """
    info_tuple = dict2tuple(data)
    info_dict = tuple2dict(info_tuple, constructor=DingoObjDict)
    return info_dict
