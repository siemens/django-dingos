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

from dingos.core.utilities import get_from_django_obj

def to_csv(objects,io_obj,headers,fields,**kwargs):

    def recursive_join(xxs,join_string):
        if isinstance(xxs,list):
            return join_string.join(map(lambda yys: recursive_join(yys,join_string),xxs))
        else:
            return str(xxs)

    # The first line (CSV) is reserved for column headers by default.
    if 'include_column_names' not in kwargs.keys() or kwargs['include_column_names'] == 'True':
        headline = []
        for header in headers:
            headline.append(header)
        io_obj.writerow(headline)

    # Data
    for object in objects:
        record = []
        multivalue_columns = []
        column_counter = 0
        for field_string in fields:
            field_components = field_string.split('.')
            result = get_from_django_obj(object,field_components)
            if isinstance(result,list):
                if len(result) > 1:
                    multivalue_columns.append(counter)

            record.append(result)


        if 'flatten' not in kwargs.keys() or kwargs['flatten'] != 'False':
            finished_columns =  []
            for column in record:
                finished_columns.append(recursive_join(column,kwargs.get('flatten',';')))
            io_obj.writerow(finished_columns)
        else:
            if len(multivalue_columns) > 1:
                raise TypeError, "Cannot flatten line in result because there is more than one multivalued column"
            else:
                #TODO: add flattening
                resulting_lines = []
                finished_columns =  []
                pass
