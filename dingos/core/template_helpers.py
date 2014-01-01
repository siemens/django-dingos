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


import collections

from types import StringType, NoneType, BooleanType

class ConfigDict_OUTDATED(object):
    """
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


class ConfigDefaultIntWrapper(int):
    def __getitem__(self,key):
        return self

class ConfigDefaultListWrapper(list):
    def __getitem__(self,key):
        return self

class ConfigDefaultStringWrapper(StringType):
    def __getitem__(self,key):
        return self


class ConfigDict(collections.Mapping):
    """

    """

    def __init__(self, *args, **kwargs):

        default = kwargs.get('default','Empty_List')
        if default == 'Empty_List':
            self.default= ConfigDefaultListWrapper([])
        else:
            try:
                default = ConfigDefaultIntWrapper(int(default))
            except:
                default = ConfigDefaultStringWrapper(default)
            self.default = default
        self.walker = kwargs.get('config_dict',dict())
        print "Initializing with default %s and walker %s" % (self.default,self.walker)

    def __iter__(self):
        #return ConfigDictIterator(self.walker)

        return self.walker.__iter__()

    def __len__(self):
        return self.walker.__len__()



    def __getitem__(self, key):
        print "Get carried out for %s" % key
        if key in self.walker:
            self.walker = self.walker[key]
            if isinstance(self.walker,basestring):
                return self.walker
            else:
                print "Returning self with default %s and walker %s" % (self.default,self.walker)
                return self
        else:
            print "Returning default %s for key %s" % (self.default.__class__, key)
            return self.default
            return {0:self.default,1:self.default}



class ConfigDictWrapper(object):
    """

    """


    def __init__(self, *args, **kwargs):
        self.config_dict = kwargs.get('config_dict',dict())

    def __getitem__(self, key):

        if key in self.config_dict:
            print "Returned config dict with default Empyt_List"
            return ConfigDict(default='Empty_List',config_dict=self.config_dict[key])
        else:
            print "Returned config dict with default %s" % key
            return ConfigDict(default=key,config_dict=self.config_dict)
