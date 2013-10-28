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
from django.core.management.base import BaseCommand, CommandError
from dingos.models import InfoObject

class Command(BaseCommand):
    """
    This class implements the command for importing a generic XML
    file into DINGO.
    """
    args = 'no arguments'
    help = """Regenerates names for all information objects. Use for testing purposes with few objects
              in database rather than for a full database -- otherwise the running time might be rather longish."""

    option_list = BaseCommand.option_list

    def handle(self, *args, **options):
        for io in InfoObject.objects.all():
            io.set_name()
            io.save()
