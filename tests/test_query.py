#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_django-dingos
------------

Tests for `django-dingos` modules module.
"""

import unittest

import os

from dingos import models

from utils import deltaCalc

from django import test

from dingos.management.commands.dingos_generic_xml_import import Command

from dingos.models import InfoObject

import pprint

from datetime import datetime

now = datetime.now()

pp = pprint.PrettyPrinter(indent=2)

def load_data(test_location=''):
    command = Command()
    command.handle(os.path.join(test_location,'tests/testdata/xml/query_test/john_smith.xml'),
                   uid='john_smith',
                   placeholder_fillers=[("color","green"),
                                        ("scope","organization1"),
                                        ("usage","FOUO")],
                   identifier_ns_uri='test.org',
                   marking_json=os.path.join(test_location,'tests/testdata/markings/query_test_marking.json'),
                   default_timestamp = '2013-04-01 00:00:01+00:00'                            
                   )

    command.handle(os.path.join(test_location,'tests/testdata/xml/query_test/john_doe.xml'),
                            uid='john_doe',
                            placeholder_fillers=[("color","yellow"),
                                                 ("scope","organization1"),
                                                 ("usage","FOUO")],
                            identifier_ns_uri='test.org',
                            marking_json=os.path.join(test_location,'tests/testdata/markings/query_test_marking.json'),
                            default_timestamp = '2013-04-02 00:00:01+00:00')

class query_Tests(test.TestCase):




    def setUp(self):
        load_data()

    def test_query_all_johns(self):

        count = InfoObject.objects.all().count()

        print "There are %s InfoObjects in the db" % count

        self.assertEqual(count,4)


        Q_dict = {'identifier__uid__contains':'john'}

        count = InfoObject.objects.filter(**Q_dict).count()

        print "There are %s objects in the db that satisfy %s" % (count,Q_dict) 
        self.assertEqual(count,2)
