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






