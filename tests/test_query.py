#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_django-dingos
------------

Tests for `django-dingos` modules module.
"""

import os
from django import test
from unittest import skip
from dingos.management.commands.dingos_generic_xml_import import Command
from dingos.models import InfoObject
import pprint
from datetime import datetime
from dingos.queryparser.queryparser import QueryParser

now = datetime.now()
pp = pprint.PrettyPrinter(indent=2)


def load_data(test_location=''):
    command = Command()
    command.handle(os.path.join(test_location, 'tests/testdata/xml/query_test/john_smith.xml'),
                   uid='john_smith',
                   placeholder_fillers=[("color", "green"),
                                        ("scope", "organization1"),
                                        ("usage", "FOUO")],
                   identifier_ns_uri='test.org',
                   marking_json=os.path.join(test_location, 'tests/testdata/markings/query_test_marking.json'),
                   default_timestamp='2013-04-01 00:00:01+00:00')
    command.handle(os.path.join(test_location, 'tests/testdata/xml/query_test/john_doe.xml'),
                   uid='john_doe',
                   placeholder_fillers=[("color", "yellow"),
                                        ("scope", "organization1"),
                                        ("usage", "FOUO")],
                   identifier_ns_uri='test.org',
                   marking_json=os.path.join(test_location, 'tests/testdata/markings/query_test_marking.json'),
                   default_timestamp='2013-04-02 00:00:01+00:00')


class QueryTests(test.TestCase):
    def setUp(self):
        load_data()

    @skip
    def test_exact(self):
        print_test_name()
        query = "identifier__uid = 'john_smith'"
        objects = parse_and_query(query)
        self.assertEqual(objects.count(), 1)
        for oneObject in objects:
            self.assertEqual(oneObject.identifier.uid, "john_smith")

    @skip
    def test_contains(self):
        print_test_name()

        query = "identifier__uid contains 'ohn_'"
        objects = parse_and_query(query)
        self.assertEqual(objects.count(), 2)
        for oneObject in objects:
            self.assertTrue("john_" in oneObject.identifier.uid)

        query = "identifier__uid contains 'OHN_'"
        objects = parse_and_query(query)
        self.assertEqual(objects.count(), 0)

        query = "identifier__uid icontains 'OHN_'"
        objects = parse_and_query(query)
        self.assertEqual(objects.count(), 2)
        for oneObject in objects:
            self.assertTrue("john_" in oneObject.identifier.uid)

    @skip
    def test_regexp(self):
        print_test_name()

        query = "identifier__uid regexp '.?ohn_.+'"
        objects = parse_and_query(query)
        self.assertEqual(objects.count(), 2)
        for oneObject in objects:
            self.assertTrue("john_" in oneObject.identifier.uid)

        query = "identifier__uid regexp '.?OHN_.+'"
        objects = parse_and_query(query)
        self.assertEqual(objects.count(), 0)

        query = "identifier__uid iregexp '.?OHN_.+'"
        objects = parse_and_query(query)
        self.assertEqual(objects.count(), 2)
        for oneObject in objects:
            self.assertTrue("john_" in oneObject.identifier.uid)

    @skip
    def test_startswith(self):
        print_test_name()

        query = "identifier__uid startswith 'john_'"
        objects = parse_and_query(query)
        self.assertEqual(objects.count(), 2)
        for oneObject in objects:
            self.assertTrue("john_" in oneObject.identifier.uid)

        query = "identifier__uid startswith 'John_'"
        objects = parse_and_query(query)
        self.assertEqual(objects.count(), 0)

        query = "identifier__uid istartswith 'John_'"
        objects = parse_and_query(query)
        self.assertEqual(objects.count(), 2)
        for oneObject in objects:
            self.assertTrue("john_" in oneObject.identifier.uid)

    @skip
    def test_endswith(self):
        print_test_name()

        query = "identifier__uid endswith 'mith'"
        objects = parse_and_query(query)
        self.assertEqual(objects.count(), 1)
        for oneObject in objects:
            self.assertTrue("john_smith" in oneObject.identifier.uid)

        query = "identifier__uid endswith 'MiTh'"
        objects = parse_and_query(query)
        self.assertEqual(objects.count(), 0)

        query = "identifier__uid iendswith 'MiTh'"
        objects = parse_and_query(query)
        self.assertEqual(objects.count(), 1)
        self.assertEqual(objects[0].identifier.uid, "john_smith")

    def test_boolop_or(self):
        print_test_name()

        query = "identifier__uid = 'john_smith' || identifier__uid = 'john_doe'"
        objects = parse_and_query(query)
        self.assertEqual(objects.count(), 2)
        for oneObject in objects:
            self.assertTrue("john_smith" in oneObject.identifier.uid or "john_doe" in oneObject.identifier.uid)

    def test_boolop_and(self):
        print_test_name()

        query = "identifier__uid startswith 'john_' && identifier__uid endswith 'doe'"
        objects = parse_and_query(query)
        self.assertEqual(objects.count(), 1)
        self.assertEqual(objects[0].identifier.uid, "john_doe")

    ''' TO TEST
    identifier__namespace__uri contains 'mandian' && [STIX_Header/Package_Intent] endswith "tors"
    [STIX_Header/Package_Intent] endswith "Indicators"
    [STIX_Header/Information_Source/Contributors/Contributor/Name] contains "MITRE (STIX Conversion)"
    [STIX_Header/Title] contains "APT1 Report"
    [Observables@cybox_major_version] = "2" || identifier__namespace__uri contains 'mandian'
    [Observables@cybox_major_version] = "2" && identifier__namespace__uri contains 'mandian'
    [Observables@cybox_major_version] = "2" | [STIX_Header/Title] contains "APT1 Report"
    [Observables@cybox_major_version] = "2" && [STIX_Header/Title] contains "APT1 Report"
    '''


    """
    for fact in oneObject.facts.all():
        out("\t%s: " % fact.fact_term)
        for value in fact.fact_values.all():
            out("\t\t%s" % value)
    """


def parse_and_query(query):
        # Parse query
        parser = QueryParser()
        out("Query:\t%s" % query)
        filter_collection = parser.parse(str(query))

        # Generate and execute query
        filter_list = filter_collection.get_filter_list()
        objects = getattr(InfoObject, 'objects').exclude(latest_of=None)
        for oneFilter in filter_list:
            out("Filter:\t%s" % oneFilter)
            objects = getattr(objects, 'filter')(oneFilter)
        objects = objects.distinct()
        out("SQL:\t%s" % objects.query)
        return objects


def print_test_name():
    import traceback
    out("Test method: %s" % traceback.extract_stack(None, 2)[0][2])


def out(value):
    print "===> %s" % value
    pass
