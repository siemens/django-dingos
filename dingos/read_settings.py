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

from django.conf import settings
from django.core.files.storage import FileSystemStorage

import dingos

if settings.configured and 'DINGOS' in dir(settings):
    dingos.DINGOS_TEMPLATE_FAMILY = settings.DINGOS.get('TEMPLATE_FAMILY', dingos.DINGOS_TEMPLATE_FAMILY)

if settings.configured and 'DINGOS' in dir(settings):
    dingos.DINGOS_DEFAULT_ID_NAMESPACE_URI = settings.DINGOS.get('OWN_ORGANIZATION_ID_NAMESPACE',
                                                                 dingos.DINGOS_DEFAULT_ID_NAMESPACE_URI)

if settings.configured and 'DINGOS' in dir(settings):
    dingos.DINGOS_BLOB_ROOT = settings.DINGOS.get('BLOB_ROOT',None)

if not dingos.DINGOS_BLOB_ROOT:

    dingos.DINGOS_BLOB_STORAGE=None
    #raise NotImplementedError("Please configure a BLOB_ROOT  directory in the DINGOS settings (look "
    #                          "at how the MEDIA directory is defined and define an appropriate directory "
    #                          "for storing stuff that does not got into the database (usually very large "
    #                          "values) on the filesystem.")
else:

    dingos.DINGOS_BLOB_STORAGE = FileSystemStorage(location=dingos.DINGOS_BLOB_ROOT)
    # We do not want the blobs to be directly available via URL.
    # Reading the code it seems that setting 'base_url=None' in
    # the __init__ arguments does not help, because __init__
    # then choses the media URL as default url. So we have
    # to set it explicitly after __init__ is done.
    dingos.DINGOS_BLOB_STORAGE.base_url=None

if settings.configured and 'DINGOS' in dir(settings):
    dingos.DINGOS_MAX_VALUE_SIZE_WRITTEN_TO_VALUE_TABLE = settings.DINGOS.get('DINGOS_MAX_VALUE_SIZE_WRITTEN_TO_VALUE_TABLE',
                                                                             dingos.DINGOS_MAX_VALUE_SIZE_WRITTEN_TO_VALUE_TABLE)

if settings.configured and 'DINGOS' in dir(settings):
    configured_large_value_dest = settings.DINGOS.get('LARGE_VALUE_DESTINATION',None)
    if configured_large_value_dest:
        if configured_large_value_dest == 'DINGOS_VALUES_TABLE':
            dingos.DINGOS_LARGE_VALUE_DESTINATION = dingos.DINGOS_VALUES_TABLE
    elif configured_large_value_dest == 'DINGOS_FILE_SYSTEM':
        dingos.DINGOS_LARGE_VALUE_DESTINATION = dingos.DINGOS_FILE_SYSTEM
    elif configured_large_value_dest == 'DINGOS_BLOB_TABLE':
        dingos.DINGOS_LARGE_VALUE_DESTINATION = dingos.DINGOS_BLOB_TABLE


