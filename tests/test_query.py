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

        # Test field
        query = "identifier__uid = 'john_smith'"
        objects = parse_and_query(query)
        self.assertEqual(objects.count(), 1)
        self.assertEqual(objects[0].identifier.uid, "john_smith")

        # Test fact term
        query = "[firstName]='John'"
        objects = parse_and_query(query)
        self.assertEqual(objects.count(), 2)
        for oneObject in objects:
            found = False
            for fact in oneObject.facts.all():
                # One of the fact terms has to be the right one
                if str(fact.fact_term) == 'firstName':
                    # One of the values has to be the right one
                    for value in fact.fact_values.all():
                        if str(value) == 'John':
                            found = True
            self.assertTrue(found)

        # Test deeper fact term
        query = "[phoneNumbers/phoneNumber]='746 555-4567'"
        objects = parse_and_query(query)
        self.assertEqual(objects.count(), 1)
        found = False
        for fact in objects[0].facts.all():
            if str(fact.fact_term) == 'phoneNumbers/phoneNumber':
                for value in fact.fact_values.all():
                    if str(value) == '746 555-4567':
                        found = True
        self.assertTrue(found)

        # Test fact attribute
        query = "[phoneNumbers/phoneNumber@type]='home'"
        objects = parse_and_query(query)
        self.assertEqual(objects.count(), 2)
        for oneObject in objects:
            found = False
            for fact in oneObject.facts.all():
                if str(fact.fact_term) == 'phoneNumbers/phoneNumber@type':
                    for value in fact.fact_values.all():
                        if str(value) == 'home':
                            found = True
            self.assertTrue(found)

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

    @skip
    def test_boolop_or(self):
        print_test_name()

        query = "identifier__uid = 'john_smith' || identifier__uid = 'john_doe'"
        objects = parse_and_query(query)
        self.assertEqual(objects.count(), 2)
        for oneObject in objects:
            self.assertTrue("john_smith" in oneObject.identifier.uid or "john_doe" in oneObject.identifier.uid)

    @skip
    def test_boolop_and(self):
        print_test_name()

        query = "identifier__uid startswith 'john_' && identifier__uid endswith 'doe'"
        objects = parse_and_query(query)
        self.assertEqual(objects.count(), 1)
        self.assertEqual(objects[0].identifier.uid, "john_doe")

        query = "identifier__uid = 'john_smith' && identifier__uid = 'john_doe'"
        objects = parse_and_query(query)
        self.assertEqual(objects.count(), 0)

        query = "[phoneNumbers/phoneNumber@type]='home' && [phoneNumbers/phoneNumber@type]='fax'"
        objects = parse_and_query(query)
        # Logical Q object behaviour! Instead of this query use a filter!
        self.assertEqual(objects.count(), 0)

        query = "identifier__uid = 'john_smith' && [phoneNumbers/phoneNumber@type]='home'"
        objects = parse_and_query(query)
        self.assertEqual(objects.count(), 1)
        self.assertEqual(objects[0].identifier.uid, "john_smith")

    @skip
    def test_filter(self):
        print_test_name()

        query = "[phoneNumbers/phoneNumber@type]='home' | [phoneNumbers/phoneNumber]='312 555-1234'"
        objects = parse_and_query(query)
        self.assertEqual(objects.count(), 1)
        self.assertEqual(objects[0].identifier.uid, "john_doe")

        query = "filter: [phoneNumbers/phoneNumber@type]='home' | filter: [phoneNumbers/phoneNumber]='312 555-1234'"
        objects = parse_and_query(query)
        self.assertEqual(objects.count(), 1)
        self.assertEqual(objects[0].identifier.uid, "john_doe")

        query = "filter: [phoneNumbers/phoneNumber@type]='home' | exclude: [phoneNumbers/phoneNumber]='312 555-1234'"
        objects = parse_and_query(query)
        self.assertEqual(objects.count(), 1)
        self.assertEqual(objects[0].identifier.uid, "john_smith")

    #@skip
    def test_not(self):
        print_test_name()

        # Test field
        query = "identifier__uid != 'john_smith'"
        objects = parse_and_query(query)
        self.assertEqual(objects.count(), 3)
        for oneObject in objects:
            self.assertNotEqual(oneObject.identifier.uid, "john_smith")

        # Test fact term
        query = "[lastName] != 'Smith'"
        objects = parse_and_query(query)
        self.assertEqual(objects.count(), 1)
        for fact in objects[0].facts.all():
            # One of the fact terms has to be the right one
            if str(fact.fact_term) == 'lastName':
                # One of the values has to be the right one
                for value in fact.fact_values.all():
                    if str(value) == 'Smith':
                        self.assertNotEqual(str(value), 'Smith')

        # Test fact term
        query = "[lastName] !icontains 'mIT'"
        objects = parse_and_query(query)
        self.assertEqual(objects.count(), 1)
        for fact in objects[0].facts.all():
            # One of the fact terms has to be the right one
            if str(fact.fact_term) == 'lastName':
                # One of the values has to be the right one
                for value in fact.fact_values.all():
                    if str(value) == 'Smith':
                        self.assertNotEqual(str(value), 'Smith')

        # Test query with boolean operator
        query = "[lastName]!='Smith' && [lastName]='Doe'"
        objects = parse_and_query(query)
        self.assertEqual(objects.count(), 1)
        found = False
        for fact in objects[0].facts.all():
            # One of the fact terms has to be the right one
            if str(fact.fact_term) == 'lastName':
                # One of the values has to be the right one
                for value in fact.fact_values.all():
                    if str(value) == 'Doe':
                        found = True
        self.assertTrue(found)

        # Test query with boolean operator
        query = "[lastName]!='Smith' && [lastName]!='Doe'"
        objects = parse_and_query(query)
        self.assertEqual(objects.count(), 0)


def parse_and_query(query):
    out()

    # Parse query
    parser = QueryParser()
    out("Query:%s" % query)
    filterCollection = parser.parse(str(query))

    # Generate and execute query
    objects = getattr(InfoObject, 'objects').exclude(latest_of=None)

    for oneFilter in filterCollection.get_filter_list():
        if oneFilter['type'] == 'filter':
            out("Filter: %s" % oneFilter['q'])
            objects = getattr(objects, 'filter')(oneFilter['q'])
        elif oneFilter['type'] == 'exclude':
            out("Exclude: %s" % oneFilter['q'])
            objects = getattr(objects, 'exclude')(oneFilter['q'])

    objects = objects.distinct()
    #out("SQL: %s" % objects.query)
    return objects


def print_test_name():
    import traceback
    print "\n======================================\nTest method: %s\n======================================" %\
          traceback.extract_stack(None, 2)[0][2]


def out(value=''):
    print "===> %s" % value
    pass
