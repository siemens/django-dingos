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

import libxml2


def extract_attributes(element, prefix_key_char='@', dict_constructor=dict):
    """
    Given an XML node, extract a dictionary of attribute key-value pairs.
    Optional arguments:

    - prefix_key_char: if a character is given, the attributes keys
      in the resulting dictionary are prefixed with that character.

    - dict_constructor: the class used to create the resulting dictionary.
      Default is 'dict', but in DINGO, also DingoObjDict may be used.
    """
    result = dict_constructor()
    if element.properties:
        for prop in element.properties:
            if not prop:
                break
            if prop.type == 'attribute':
                try:
                    # First try with namespace. If no namespace exists,
                    # an exception is raised
                    result["%s%s:%s" % (prefix_key_char, prop.ns().name, prop.name)] = prop.content
                except:
                    result["%s%s" % (prefix_key_char, prop.name)] = prop.content
    return result
