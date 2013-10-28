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


import pprint

pp = pprint.PrettyPrinter(indent=2)

def print_arguments():
    """
    Decorator that provides the wrapped function with an attribute 'print_arguments'
    containing just those keyword arguments actually passed in to the function.

    To use the decorator for debugging, preface the function into whose calls
    you are interested with '@print_arguments()'
    """
    def decorator(function):
        def inner(*args, **kwargs):
            if args:
                print "Passed arguments:"
                for i in args:
                    pp.pprint(i)
            print "Passed keyword arguments:"
            pp.pprint(kwargs)
            return function(*args, **kwargs)
        return inner
    return decorator