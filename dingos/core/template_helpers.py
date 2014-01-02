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


import collections
import logging

from types import StringType, NoneType, BooleanType

logger = logging.getLogger(__name__)

class ConfigDict_OUTDATED(object):
    """

    First attempt by ckoepp.

    A helper class for using customized
    configurations within django views
    """

    _orig_dict =  None
    _stack = []

    def __init__(self, orig_dict):
        """
        Needs to receive a dict-like object for init.
        Note that it works with all dict-like objects WITHOUT a boolean as key!
        """
        self._orig_dict = orig_dict

    def get(self, key):
        """ Just a wrapper for __getitem__() """
        return self.__getitem__(key)

    def _clear_stack(self):
        """ Just clears the stack and returns it's last value (centralized method) """
        out = self._stack[len(self._stack)-1]
        self._stack = []
        return out

    def __getitem__(self, key):
        """
        Returns itself until a "True" is given as key (as String instance).
        In this very case all the former called keys are being tried.
        If the path turns out to return a valid object it is returned.
        Otherwise the SECOND LAST key argument (the one BEFORE bool) will
        be returned as it represents the default value.

        Example usage:
          this_dict = ConfigDict({ 'first' : { 'second' : 20 } })
          this_dict.get('first').get('second').get(1).get("True")
          returns 20 instead of the 1 (which represents the default value)
        """

        # no bool? just append element and return yourself
        if not key == "True":
            self._stack.append(key)
            return self

        print self._stack
        # time to create an output by going along stack (last element of stack is DEFAULT value!)
        current_element = self._orig_dict
        for i in range(0, len(self._stack)-1):
            try:
                current_element = current_element[self._stack[i]]

            # exception raised (TypeError or KeyError)? Return default value
            except Exception as e:
                return self._clear_stack()

        return self._clear_stack()


class ConfigDict(collections.Mapping):
    """
    A wrapper for a dictionary structure that supports the following behavior
    when accessing the structure in a Django template: ``configdict.path.to.the.value.in.dict``
    will yield the value of ``configdict['path']['to']['the']['value']['in']['dict'], if
    such a value exists. Otherwise, it will return a default value with which the
    ``ConfigDict`` has been instantiated at creation.

    Note that the dictionaries treated with ConfigDict may only contain strings as 'leafs';
    strings that can be converted to an integer will be converted to an integer. So, in
    order to express 'True' and 'False', use '1' and '0'.

    Use the class as follows:

    wrapped_dict = ConfigDict(default=<default value>,config_dict=<dictionary to be wrapped>)

    Note that the string ``Empty_List`` as default value will chose an empty list as
    default value -- this can be handy if the value retrieved from the dictionary is
    to be used in a ``for .. in`` construction in the template.
    """

    def __init__(self, *args, **kwargs):

        default = kwargs.get('default','Empty_List')
        # The string 'Empty_List' is special in that it signifies an empty list as
        # default value. We chose this as default default value, because it supports
        # the ``for ... in`` usage with may occur in a template.

        if default == 'Empty_List':
            self.default= ConfigDefaultListWrapper([])
        else:
            try:
                # Try to convert to integer
                default = ConfigDefaultIntWrapper(int(default))
            except:
                default = ConfigDefaultStringWrapper(default)
            # As you see above: whatever default value we set: we have
            # wrapped it in a special class. This class does nothing but
            # providing the ``__getitem__` method that returns ``self`` for
            # any key. Thus, the template can work its way through a
            # non-existing dictionary path ... and at the end, the default
            # value is returned.
            self.default = default
        self.walker = kwargs.get('config_dict',dict())
        logger.debug("Initializing ConfigDict %s with default %s and walker %s" % (self, self.default,self.walker))

    def __iter__(self):

        return self.walker.__iter__()

    def __len__(self):
       return self.walker.__len__()

    def __getitem__(self, key):
        logger.debug("Get carried out on ConfigDict %s for %s" % (self,key))
        if key in self.walker:
            self.walker = self.walker[key]
            if isinstance(self.walker,basestring):
                # We have reached a leaf in the dictionary
                return self.walker
            else:
                logger.debug("Returning self %s with default %s and walker %s" % (self,self.default,self.walker))
                return self
        else:
            logger.debug("Returning from %s default %s for key %s" % (self,self.default, key))
            return self.default

    def __unicode__(self):
        return "%s" % self.walker

class ConfigDefaultIntWrapper(int):
    """
    Add the ``__getitem__`` method to an integer, that always returns ``self``.

    Thus, the template can work its way through a
    non-existing dictionary path ... and at the end, the default
    value is returned.
    """
    def __getitem__(self,key):
        return self


class ConfigDefaultListWrapper(list):
    """
    Add ``__getitem__`` method to  list, that always returns ``self``.

    Thus, the template can work its way through a
    non-existing dictionary path ... and at the end, the default
    value is returned.

    Note: this should only be used on the empty list!
    """
    def __getitem__(self,key):
        return self

class ConfigDefaultStringWrapper(StringType):
    """
    Add the ``__getitem__`` method to a string, that always returns ``self``.

    Thus, the template can work its way through a
    non-existing dictionary path ... and at the end, the default
    value is returned.
    """
    def __getitem__(self,key):
        return self

class ConfigDictWrapper(object):
    """
    A wrapper for a dictionary structure that supports the following behavior
    when accessing the structure in a Django template: ``configdict.default_value.path.to.the.value.in.dict``
    will yield the value of ``configdict['path']['to']['the']['value']['in']['dict'], if
    such a value exists. Otherwise, it will return ``default_value`` (if the default value
    looks like an integer, it is converted to an integer).

    Note that the dictionaries treated with ConfigDict may only contain strings as 'leafs';
    strings that can be converted to an integer will be converted to an integer. So, in
    order to express 'True' and 'False', use '1' and '0'.

    Use the class as follows:

    wrapped_dict = ConfigDictWrapper(config_dict=<dictionary to be wrapped>)

    Note that the string ``Empty_List`` as default value will chose an empty list as
    default value -- this can be handy if the value retrieved from the dictionary is
    to be used in a ``for .. in`` construction in the template.
    """

    def __init__(self, *args, **kwargs):
        self.config_dict = kwargs.get('config_dict',dict())

    def __getitem__(self, key):

        # Uncommenting the code below and making the following code the else branch
        # will support a default default value ``Empty_List``, if it looks like
        # the first element in the row of '.'-access-elements might be part of
        # the path rather than a default value. But currently, we think that
        # an explicit default value should always be provided in a template.
        #
        # if key in self.config_dict:
        #    return ConfigDict(default='Empty_List',config_dict=self.config_dict[key])
        # else:
        logger.debug("Wrapped config dict with default %s" % key)
        return ConfigDict(default=key,config_dict=self.config_dict)

    def __unicode__(self):
        return "%s" % self.config_dict