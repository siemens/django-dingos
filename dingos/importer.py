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
import hashlib
import getpass
import os
import re
import json
import glob
import traceback
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from dingos.core.decorators import print_arguments

from dingos.core.datastructures import dict2DingoObjDict
from dingos import *
from dingos.import_handling import DingoImportHandling


DingoImporter = DingoImportHandling()

logger = logging.getLogger(__name__)


class Generic_XML_Import:
    """
    This class provides the xml_import function for
    generic XML import into DINGO.

    This class can be used
    as template for defining specialized XML importers
    that have knowledge of the XML they are importing
    (e.g., are able to determine identifiers and timestamps,
    extract embedded objects, etc.). Have a look
    at the MANTIS importer for IODEF for an example
    of an importer with only moderate amounts of
    configuration.
    """
    def __init__(self, *args, **kwargs):

        # We keep track of toplevel attributes
        # and namespace info

        self.toplevel_attrs = {}
        self.namespace_dict = {}


    #
    # Now, we define functions for the hooks provided to us
    # by the DINGO xml-import. For the generic import
    # there is almost nothing to be done.



    def id_and_revision_extractor(self, xml_elt):
        """
        Function for generating a unique identifier for extracted embedded content;
        to be used for DINGO's xml-import hook 'embedded_id_gen'.

        For generic import, this function should be called exactly once, namely
        on the root element, but we ignore the result and rather derive
        a identifier from the hash value of the imported file.

        """

        return {'id': None,
                'timestamp': None,
        }


    def cybox_embedding_pred(self, parent, child, ns_mapping):
        """
        Predicate for recognizing inlined content in an XML; to
        be used for DINGO's xml-import hook 'embedded_predicate'.

        The generic importer does not recognize anything as embedded.
        """

        return False


    def ft_handler_list(self):
        """
        The fact-term handler list consists of a pairs of predicates
        and functions to be called on facts before they are created.
        These handlers can modify facts. For the generic import,
        nothing is done.
        """
        return []

    def datatype_extractor(self, iobject, fact, attr_info, namespace_mapping, add_fact_kargs):
        """
        The datatype extractor can be used to determine the data type of
        values based on contextual information. For the generic XML import, we
        know nothing about data types and simply return False in order to
        signify that no data type information could be established.

        """
        return False


    def xml_import(self,
                   filepath=None,
                   xml_content = None,
                   markings=None,
                   identifier_ns_uri = None,
                   uid = None,
                   **kargs):

        """
        Call this function for generic import of an XML file with the following arguments:

        - filename: Path to XML file
        - markings (optional): List of information objects with which the imported object
          should be marked
        - identifier_ns_uri: Namespace of the identifiers, if identifiers are to be created
        - uid (optional): unique identifier -- if none is given, the SHA256 of the file
          contents are used as identifier.
         """


        # Reset bookkeeping dictionaries


        if not markings:
            markings = []
        if not identifier_ns_uri:
            identifier_ns_uri = DINGOS_DEFAULT_ID_NAMESPACE_URI

        self.__init__()

        # Carry out generic XML import
        import_result = DingoImporter.xml_import(xml_fname=filepath,
                                                 xml_content=xml_content,
                                                 ns_mapping=self.namespace_dict,
                                                 embedded_predicate=self.cybox_embedding_pred,
                                                 id_and_revision_extractor=self.id_and_revision_extractor)


        # Extract data required for creating info object

        id_and_rev_info = import_result['id_and_rev_info']
        elt_name = import_result['elt_name']
        elt_dict = import_result['dict_repr']
        file_content = import_result['file_content']

        if uid:
            id_and_rev_info['id'] = uid
        else:
            id_and_rev_info['id'] = hashlib.sha256(file_content).hexdigest()

        id_and_rev_info['timestamp'] = timezone.now()

        create_timestamp = id_and_rev_info['timestamp']

        iobject_family_name = self.namespace_dict.get(elt_dict.get('@@ns', None), DINGOS_GENERIC_FAMILY_NAME)

        iobject_family_revision_name = ''
        iobject_type_name = elt_name
        iobject_type_namespace_uri = self.namespace_dict.get(elt_dict.get('@@ns', None), DINGOS_GENERIC_FAMILY_NAME)

        # Create info object

        DingoImporter.create_iobject(iobject_family_name=iobject_family_name,
                                     iobject_family_revision_name=iobject_family_revision_name,
                                     iobject_type_name=iobject_type_name,
                                     iobject_type_namespace_uri=iobject_type_namespace_uri,
                                     iobject_type_revision_name='',
                                     iobject_data=elt_dict,
                                     uid=id_and_rev_info['id'],
                                     identifier_ns_uri=identifier_ns_uri,
                                     timestamp=id_and_rev_info['timestamp'],
                                     create_timestamp=create_timestamp,
                                     markings=markings,
                                     config_hooks={'special_ft_handler': self.ft_handler_list(),
                                                   'datatype_extractor': self.datatype_extractor},
                                     namespace_dict=self.namespace_dict,
        )


class DingoImportCommand(BaseCommand):
    """
    This class serves as basis for import commands that are specified
    in the management/commands directory of a Django app using DINGO
    for imports.

    It basically adds the following command line arguments and associated
    processing to the Dingo.BaseCommand class:

    - `--marking_json` is used to specify a json file that contains
      data for an information object with which all information objects
      generated by the XML import are to be marked. Here is an example
      the contents of such a json file::

           {"Mechanism" : {"Category":"Commandline Import",
                           "User": "DINGO[_username]",
                           "Commandline": {"Command":"DINGO[_command]",
				           "KeywordArguments":"DINGO[_kargs]",
				           "Arguments":"DINGO[_args]"}
	                      },
          "Source" : "DINGO[source]"}

      As becomes apparent above, the JSON may contain placeholders.
      of form 'DINGO[<placeholder_name>]'. Placeholders with names
      that start with a '_' are filled in automatically -- the definition
      for user-defined placeholders is provided with the
      command-line argument --marking-pfill.

    - `--marking-pfill` takes a list of arguments that are processed pairwise:
      the first component of each pair is interpreted as placeholder name,
      the second as value to fill in for that placeholder.

      To fill in the 'source' placeholder in the above example, you
      might call the command line with::

                  --marking-pfill  source "Regular import from Malware Sandbox"

      Be sure to encompass placeholder values in quotation marks
      (If you are using PyCharm as IDE: note that PyCharm messes up quoted
      commandline arguments in its run configuration -- you have to test
      that stuff from a true commandline).
    - `--id-namespace-uri` stores URI for namespace to be used for qualifying
         the identifiers of the information objects.
    """
    args = 'xml-file xml-file ... (you can use wildcards)'
    help = 'Imports xml files of specified paths into DINGO with generic import'

    RE_SEARCH_PLACEHOLDERS = re.compile(r"DINGO\[(?P<bla>[^\]]+)\]")

    option_list = BaseCommand.option_list + (
        make_option('-m', '--marking_json',
                    action='store',
                    dest='marking_json',
                    default=None,
                    help='File with json representation of information of marking to be associated with imports.'),
        make_option('-p', '--marking_pfill',
                    action='append',
                    nargs=2,
                    default=[],
                    dest='placeholder_fillers',
                    help='Key-value pairs used to fill in placeholders in marking as described in marking file.'),
        make_option('-n','--id_namespace_uri',
                    action='store',
                    default=None,
                    dest='identifier_ns_uri',
                    help='URI of namespace used to qualify the identifiers of the created information objects.'),
    )


    Importer = Generic_XML_Import()


    def __init__(self, *args, **kwargs):
        self.xml_import_function = kwargs.get('import_function', None)
        try:
            del (kwargs['import_function'])
        except:
            pass
        super(DingoImportCommand,self).__init__(*args,**kwargs)

    def create_import_marking(self, args, options):
        """
        This function parses the `--marking_json` and `--marking_pfill` arguments
        and creates a marking object if these parameters are specified.

        Look into 'dingos/management/commands/dingos_generic_xml_import.py to see how
        this is used to specify a Django command line argument 'dingos_generic_xml_import'
        that can be called with Django's 'manage.py'
        """
        marking_json = None
        placeholder_dict = {}

        if options.get('marking_json'):
            # Open json
            with open(options['marking_json'], 'r') as content_file:
                marking_json = content_file.read()

            del(options['marking_json'])

            # Find all placeholders
            placeholders = self.RE_SEARCH_PLACEHOLDERS.findall(marking_json)

            # Create prefilled dictionary so that later when we use
            # the json text as format string we do not encounter problems
            # for undefined placeholders.

            if placeholders:

                for placeholder in placeholders:
                    placeholder_dict[placeholder] = 'EMPTY'

        # Read in command-line specified placeholder values.
        if options.get('placeholder_fillers'):
            for (placeholder, value) in options['placeholder_fillers']:
                placeholder_dict[placeholder] = value

            del(options['placeholder_fillers'])

        # Add standard values (this list may grow in future)
        placeholder_dict['_username'] = getpass.getuser()
        placeholder_dict['_command'] = os.path.basename(__file__)
        placeholder_dict['_kargs'] = "%s" % options
        placeholder_dict['_args'] = args

        if marking_json:
            # Massage the json text such that we can use it as format string
            # to fill in the placeholders

            # Escape possible '%'
            marking_json = marking_json.replace('%','\%')
            # Replace placeholder definitions with python string formatting
            marking_json = self.RE_SEARCH_PLACEHOLDERS.sub("%(\\1)s", marking_json)

            # Use string formatting to fill in placeholders

            marking_json = marking_json % placeholder_dict

            # Finally, parse json
            marking_dict = dict2DingoObjDict(json.loads(marking_json))

            # Create info object for marking
            marking = DingoImporter.create_marking_iobject(metadata_dict=marking_dict)

            return marking

        return None

    def handle(self, *args, **options):
        # The function create_import_marking inherited from
        # DingoImport command is able to create a dictionary
        # structure for a marking with object resulting
        # from the import command will be marked.

        marking = self.create_import_marking(args,options)

        if marking:
            markings = [marking]
        else:
            markings = []

        #if len(args) > 1 and options['identifier']:
        #    raise CommandError('Option --identifier not supported for more than one file per import.')

        if len(args) == 0:
            logger.warning("No files for import specified!")
        else:
            for arg in args:
                logger.info("Starting processing")

                if len(glob.glob(arg)) == 0:
                    logger.warning("No file(s) %s for import found!" % arg)

                for filename in glob.glob(arg):

                    logger.info("Starting import of %s" % filename)

                    self.Importer.xml_import(filepath = filename,
                                             markings = markings,
                                             **options)
