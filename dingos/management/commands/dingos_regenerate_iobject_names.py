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

from django.utils.timezone import now
from datetime import timedelta

class Command(BaseCommand):
    """
    This class implements the command for importing a generic XML
    file into DINGO.
    """
    args = 'no arguments'
    help = """Regenerates names for all information objects. Use for testing purposes with few objects
              in database rather than for a full database -- otherwise the running time might be rather longish."""

    option_list = BaseCommand.option_list + (
        make_option('-r', '--restrict-to-type-name',
                action='store',
                dest='restrict_by',
                default=None,
                help='String according to which the InfoObjects for which the name is to be generated'
                     'are restricted: only those InfoObjects are touched '
                     'types whose type name contains the provided expression.'),
        make_option('-a', '--age_in_hours',
                action='store',
                dest='hours_age',
                default=None,
                help='Time span according to which the InfoObjects for which the name is to be generated'
                     'are restricted: only those InfoObjects are touched '
                     'types whose IMPORT date lies no more than the provided number of hours in the past.'),
    )


    def handle(self, *args, **options):
        if options['hours_age']:
            iobjects = InfoObject.objects.filter(iobject_type__name__icontains=options['restrict_by'],create_timestamp__gt=now() - timedelta(hours=int(options['hours_age'])))
        else:
            iobjects = InfoObject.objects.filter(iobject_type__name__icontains=options['restrict_by'])
        for io in iobjects:
            current_name = io.name
            print "Renaming %s with current name %s" % (io.identifier.uid,io.name)
            io.set_name()
            print "Renaming %s from %s to %s. " % (io.identifier.uid,current_name,io.name)
