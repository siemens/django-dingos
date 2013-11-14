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

import sys
import pprint
import json
import re

from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

from dingos.models import InfoObjectType, InfoObjectNaming, DataTypeNameSpace, InfoObjectFamily

pp = pprint.PrettyPrinter(indent=2)

class Command(BaseCommand):
    """

    """
    args = ''
    help = 'Export and import of naming schemas'

    option_list = BaseCommand.option_list + (
        make_option('-o', '--output-file',
                    action='store',
                    dest='output_file',
                    default=None,
                    help='File to which naming info is to be written. If this parameter is provided, '
                         'the currently active naming schemas are exported. You can provide this '
                         'parameter together with the -i parameter: in this case, the curren state '
                         'is written to the output file before doing the import'),
        make_option('-i', '--input-file',
                    action='store',
                    dest='input_file',
                    default=None,
                    help='File from which naming info is to be read.'),
        make_option('-r', '--restrict-to-family',
                    action='store',
                    dest='restrict_regexp',
                    default=None,
                    help='Regular expression by which the InfoObject types for which' \
                         'import/export is to be performed is restricted: only those InfoObjects are touched ' \
                         'types whose family name contains a match of the provided regular expression.'),


    )


    def __init__(self, *args, **kwargs):
        self.schemas = kwargs.get('schemas', None)
        try:
            del (kwargs['schemas'])
        except:
            pass
        super(Command,self).__init__(*args,**kwargs)

    def handle(self, *args, **options):

        iobject_types = InfoObjectType.objects.all()


        if not 'input_list' in options:
            options['input_list'] = None

        if options.get('output_file',None) and \
                (options.get('input_file',None) == options['output_file']):
            raise CommandError("Please specify different input and output files!")

        if options.get('restrict_regexp',None):
            re_restrict_family = re.compile(options['restrict_regexp'])

        if options.get('output_file',None):
            print "Exporting naming schemas"

            # Write the existing naming schemas to the output file
            result_list = []
            for iobject_type in iobject_types:
                if not options.get('restrict_regexp',None) or re_restrict_family.search(iobject_type.iobject_family.name):
                    schema_list = []
                    name_schemas = InfoObjectNaming.objects.filter(iobject_type=iobject_type).order_by(
                        'position').values_list('format_string', flat=True)
                    result_list.append((iobject_type.name, iobject_type.iobject_family.name, iobject_type.namespace.uri,list(name_schemas)))

            with open(options['output_file'], 'w') as outfile:
                json.dump(result_list, outfile, indent=4)

        if options.get('input_file',None) or options.get('input_list',None):
            print "Importing naming schemas."
            # Read naming schemas and import them
            if options['input_list']:
                naming_list = self.schemas
            else:
                with open(options['input_file'], 'r') as content_file:
                    json_string = content_file.read()
                    naming_list = json.loads(json_string)


            for iobject_type_info in naming_list:
                name,family_name,iodt_ns_uri,naming_list = iobject_type_info
                if not options.get('restrict_regexp',None) or re_restrict_family.search(family_name):
                    iodt_ns, created = DataTypeNameSpace.objects.get_or_create(uri=iodt_ns_uri)
                    iodt_family, created = InfoObjectFamily.objects.get_or_create(name=family_name)
                    iobject_type, created = InfoObjectType.objects.get_or_create(name=name,
                                                                        iobject_family=iodt_family,
                                                                        namespace=iodt_ns)
                    # Delete existing naming schemas
                    InfoObjectNaming.objects.filter(iobject_type=iobject_type).delete()
                    counter = 0
                    # Create naming schemas as specified in input file
                    for naming_schema in naming_list:
                        InfoObjectNaming.objects.create(iobject_type=iobject_type,
                                                        position=counter,
                                                        format_string=naming_schema)

                        counter += 1



