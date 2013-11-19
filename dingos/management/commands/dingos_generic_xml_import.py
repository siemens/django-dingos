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


import glob
import traceback

from optparse import make_option
from django.core.management.base import CommandError
from dingos.importer import Generic_XML_Import, DingoImportCommand



class Command(DingoImportCommand):
    """
    This class implements the command for importing a generic XML
    file into DINGO.
    """
    args = 'path/to/xml-file path/to/xml-file ... (you can use wildcards)'
    help = 'Imports xml files of specified paths into DINGO'

    option_list = DingoImportCommand.option_list + (
        make_option('-i', '--identifier',
                    action='store',
                    dest='uid',
                    default=None,
                    help="""Unique identifier for imported information object (optional: otherwise the SHA256
                            of the file contents is used. Only possible if exactly one file is specified."""),
    )

    # def handle(self, *args, **options):
    #
    #     # The function create_import_marking inherited from
    #     # DingoImport command is able to create a dictionary
    #     # structure for a marking with object resulting
    #     # from the import command will be marked.
    #
    #     marking = self.create_import_marking(args,options)
    #
    #     if marking:
    #         markings = [marking]
    #     else:
    #         markings = []
    #
    #     if len(args) > 1 and options['identifer']:
    #         raise CommandError('Option --identifier not supported for more than one file per import.')
    #
    #     for arg in args:
    #         print "Starting processing"
    #         for filename in glob.glob(arg):
    #             try:
    #                 print "Starting import of %s" % filename
    #                 GenericImporter = Generic_XML_Import()
    #                 GenericImporter.xml_import(filename,markings,uid=options['identifier'])
    #             except Exception, err:
    #                 print traceback.format_exc()
    #                 print Exception, err
    #                 raise CommandError('Error %s occurred for %s' % (err,filename))
