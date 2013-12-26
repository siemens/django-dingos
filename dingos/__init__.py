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




__version__ = '0.1.0'

REVISION = __version__


# Below, default values used in DINGO are defined.


# Dingos allows for extensions with another template basis othan the
# Grappelli templates that are used by default. Such an extension
# would have to create a 'dingos/templates/<extension_name>' directory
# and reimplement the existing Dingos template structure in that
# directory.

DINGOS_TEMPLATE_FAMILY  = 'grappelli'

# The namespace uri should be used for qualifying identifiers if
# neither namespace nor namespace uri is explicitly provided for an identifier.

DINGOS_DEFAULT_ID_NAMESPACE_URI = 'enter.a.value.in.settings'


# The DINGOS_MISSING_ID_NAMESPACE_URI_PREFIX should be used s prefix for namespace
# information used in identifiers for which no namespace uri can be determined.

DINGOS_MISSING_ID_NAMESPACE_URI_PREFIX = 'https://github.com/siemens/django-dingos/wiki/namespaces_identifiers_missing'


# The DINGOS_NAMESPACE is used as default namespace for
# datatypes and information-object types created by DINGO.

DINGOS_NAMESPACE_URI = 'https://github.com/siemens/django-dingos/wiki/namespaces_dingos_types'
DINGOS_NAMESPACE_SLUG = 'DingosDefaultNameSpace'

DINGOS_DEFAULT_FACT_DATATYPE = 'String'

# The DINGOS_ID_NAMESPACE_URI is used as qualifier for identifiers
# of internal objects created by DINGO, such as information
# objects containing meta data of relations.

DINGOS_ID_NAMESPACE_URI = 'https://github.com/siemens/django-dingos/wiki/namespaces_dingos_identifiers'
DINGOS_ID_NAMESPACE_SLUG = 'DingosDefaultIdNameSpace'


# The DINGOS_GENERIC_FAMILY is used to provide a default family name for generic imports

DINGOS_GENERIC_FAMILY_NAME = 'generic'

# The DINGOS_IOBJECT_FAMILY_NAME is used as family name for all internally created objects
# such as PLACEHOLDERS. We Dingo's revision both as revision for families and object types
# of internally created information objects.

DINGOS_IOBJECT_FAMILY_NAME = 'DINGOS'

DINGOS_REVISION_NAME = REVISION

# Below, we define names used for internally created objects:

DINGOS_RELATION_TYPE_FACTTERM_NAME = '@@RelationType'

DINGOS_RELATION_METADATA_OBJECT_TYPE_NAME = 'RelationMetadata'

DINGOS_PLACEHOLDER_TYPE_NAME = 'PLACEHOLDER'

DINGOS_DEFAULT_IMPORT_MARKING_TYPE_NAME = "ImportInfo"


DINGOS_CONFIGURATION_TYPE_NAME = 'USER_CONFIG'


# Values larger than DINGOS_MAX_VALUE_SIZE_WRITTEN_TO_DB are
# not written to the data base but stored on the file system or
# written to a special blob table

DINGOS_MAX_VALUE_SIZE_WRITTEN_TO_VALUE_TABLE = 2048


# values for the LARGE_VALUE_DESTINATION are 'BLOB_TABLE' and 'FILE_SYSTEM'

DINGOS_VALUES_TABLE = 0
DINGOS_FILE_SYSTEM = 1
DINGOS_BLOB_TABLE = 2

DINGOS_LARGE_VALUE_DESTINATION = DINGOS_BLOB_TABLE



# The DINGOS_BLOB_ROOT absolutely has to be set in the DINGOS settings.
# If that is not the case, the attempt to read the value from the settings

DINGOS_BLOB_ROOT = None

# read_settings.py will instantiate the DINGOS_BLOB_STORAGE with a file storage handler
# that can also be used by importers to write file content to disk.

DINGOS_BLOB_STORAGE = None



