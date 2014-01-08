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

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, Group
from optparse import make_option

from dingos.models import UserData


from dingos import DINGOS_DEFAULT_USER_PREFS, DINGOS_USER_PREFS_TYPE_NAME, DINGOS_SAVED_SEARCHES_TYPE_NAME, DINGOS_DEFAULT_SAVED_SEARCHES

pp = pprint.PrettyPrinter(indent=2)

class Command(BaseCommand):
    """

    """
    args = 'user_name user_name user_name ...'
    help = 'Reset user customizations for specified users'

    option_list = BaseCommand.option_list + (
        make_option('-r', '--reset',
                    action='store',
                    dest='reset_target',
                    choices=['preferences', 'saved_searches', 'all'],
                    help="Set to 'all',  'preferences' or 'saved_searches' to indicated user data to be reset for specified users."),

    )



    def handle(self, *args, **options):
        if len(args) == 0:
            print "Please specify one or more user names."
            sys.exit(0)
        if 'reset_target' in options:
            if options['reset_target'] in ['preferences','saved_searches', 'all']:
                for user_name in args:
                    user = None
                    try:
                        user = User.objects.get(username=user_name)
                    except ObjectDoesNotExist:
                        pass
                    if user:
                        if options['reset_target'] in ['preferences','all']:
                            UserData.store_user_data(user=user,
                                                     data_kind=DINGOS_USER_PREFS_TYPE_NAME,
                                                     user_data=DINGOS_DEFAULT_USER_PREFS,
                                                     iobject_name = "User preferences of user '%s'" % user_name)
                            print "Resetting user preferences for user %s." % user_name
                        if options['reset_target'] in ['saved_searches','all']:
                            UserData.store_user_data(user=user,
                                                     data_kind=DINGOS_SAVED_SEARCHES_TYPE_NAME,
                                                     user_data=DINGOS_DEFAULT_SAVED_SEARCHES,
                                                     iobject_name = "Saved searches of user '%s'" % user_name)
                            print "Resetting saved searches for user %s." % user_name
            else:
                print "Please specify valid option for reset."


        else:
            print "Please specify one of the options (do --help to get an overview of available options.)"





