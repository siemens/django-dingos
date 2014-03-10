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
import re

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
    command = Command()
    command.handle(os.path.join(test_location, 'tests/testdata/xml/query_test/john_doe.xml'),
                   uid='john_doe',
                   placeholder_fillers=[("color", "yellow"),
                                        ("scope", "organization1"),
                                        ("usage", "FOUO")],
                   identifier_ns_uri='test.org',
                   marking_json=os.path.join(test_location, 'tests/testdata/markings/query_test_marking.json'),
                   default_timestamp='2013-04-02 00:00:01+00:00')
    command = Command()
    command.handle(os.path.join(test_location, 'tests/testdata/xml/query_test/max_mustermann.xml'),
                   uid='max_mustermann',
                   placeholder_fillers=[("color", "yellow"),
                                        ("scope", "organization3"),
                                        ("usage", "FOUO")],
                   identifier_ns_uri='test.org',
                   marking_json=os.path.join(test_location, 'tests/testdata/markings/query_test_marking.json'),
                   default_timestamp='2013-04-02 00:00:01+00:00')


class QueryTests(test.TestCase):
    def setUp(self):
        load_data()

    #@skip
    def test_exact(self):
        print_test_name()

        # Test field
        query = "identifier__uid = 'john_smith'"
        objects = parse_and_query(query)
        for oneObject in objects:
            self.assertEqual(oneObject.identifier.uid, "john_smith")

        # Test fact term
        query = "[firstName]='John'"
        objects = parse_and_query(query)
        for oneObject in objects:
            self.assertTrue(is_term_fact_value(oneObject, 'firstName', 'John'))

        # Test deeper fact term
        query = "[phoneNumbers/phoneNumber]='746 555-4567'"
        objects = parse_and_query(query)
        for oneObject in objects:
            self.assertTrue(is_term_fact_value(oneObject, 'phoneNumbers/phoneNumber', '746 555-4567'))

        # Test fact attribute
        query = "[phoneNumbers/phoneNumber@type]='home'"
        objects = parse_and_query(query)
        for oneObject in objects:
            self.assertTrue(is_term_fact_value(oneObject, 'phoneNumbers/phoneNumber@type', 'home'))

    #@skip
    def test_contains(self):
        print_test_name()

        query = "identifier__uid contains 'ohn_'"
        objects = parse_and_query(query)
        for oneObject in objects:
            self.assertTrue("ohn_" in oneObject.identifier.uid)

        query = "identifier__uid contains 'OHN_'"
        objects = parse_and_query(query)
        for oneObject in objects:
            self.assertTrue("OHN_" in oneObject.identifier.uid)

        query = "identifier__uid icontains 'OHN_'"
        objects = parse_and_query(query)
        for oneObject in objects:
            self.assertTrue("ohn_".upper() in oneObject.identifier.uid.upper())

    #@skip
    def test_regexp(self):
        print_test_name()

        query = "identifier__uid regexp '.?ohn_.*'"
        objects = parse_and_query(query)
        for oneObject in objects:
            self.assertTrue(re.match(".?ohn_.*", oneObject.identifier.uid))

        query = "identifier__uid regexp '.?OHN_.+'"
        objects = parse_and_query(query)
        for oneObject in objects:
            self.assertTrue(re.match(".?OHN_.*", oneObject.identifier.uid))

        query = "identifier__uid iregexp '.?OHN_.+'"
        objects = parse_and_query(query)
        for oneObject in objects:
            self.assertTrue(re.match(".?OHN_.*", oneObject.identifier.uid, flags=re.I))

    #@skip
    def test_startswith(self):
        print_test_name()

        query = "identifier__uid startswith 'john_'"
        objects = parse_and_query(query)
        for oneObject in objects:
            self.assertTrue(re.match("john_.*", oneObject.identifier.uid))

        query = "identifier__uid startswith 'John_'"
        objects = parse_and_query(query)
        for oneObject in objects:
            self.assertTrue(re.match("John_.*", oneObject.identifier.uid))

        query = "identifier__uid istartswith 'John_'"
        objects = parse_and_query(query)
        for oneObject in objects:
            self.assertTrue(re.match("John_.*", oneObject.identifier.uid, flags=re.I))

    #@skip
    def test_endswith(self):
        print_test_name()

        query = "identifier__uid endswith 'mith'"
        objects = parse_and_query(query)
        for oneObject in objects:
            self.assertTrue(re.match(".*mith", oneObject.identifier.uid))

        query = "identifier__uid endswith 'MiTh'"
        objects = parse_and_query(query)
        for oneObject in objects:
            self.assertTrue(re.match(".*MiTh", oneObject.identifier.uid))

        query = "identifier__uid iendswith 'MiTh'"
        objects = parse_and_query(query)
        for oneObject in objects:
            self.assertTrue(re.match(".*MiTh", oneObject.identifier.uid, flags=re.I))

    #@skip
    def test_boolop_or(self):
        print_test_name()

        query = "identifier__uid = 'john_smith' || identifier__uid = 'john_doe'"
        objects = parse_and_query(query)
        for oneObject in objects:
            self.assertTrue("john_smith" == oneObject.identifier.uid or "john_doe" == oneObject.identifier.uid)

    #@skip
    def test_boolop_and(self):
        print_test_name()

        query = "identifier__uid startswith 'john_' && identifier__uid endswith 'doe'"
        objects = parse_and_query(query)
        for oneObject in objects:
            self.assertTrue(re.match("john_.*", oneObject.identifier.uid))
            self.assertTrue(re.match(".*doe", oneObject.identifier.uid))

        query = "identifier__uid = 'john_smith' && identifier__uid = 'john_doe'"
        objects = parse_and_query(query)
        # Logical behaviour because 'john_smith'!='john_doe'
        self.assertEqual(objects.count(), 0)

        query = "[phoneNumbers/phoneNumber@type]='home' && [phoneNumbers/phoneNumber@type]='fax'"
        objects = parse_and_query(query)
        # Logical Q object behaviour! Instead of this query use a filter!
        self.assertEqual(objects.count(), 0)

        query = "identifier__uid = 'john_smith' && [phoneNumbers/phoneNumber@type]='home'"
        objects = parse_and_query(query)
        for oneObject in objects:
            self.assertEqual("john_smith", oneObject.identifier.uid)

    #@skip
    def test_filter(self):
        print_test_name()

        query = "[phoneNumbers/phoneNumber@type]='home' | [phoneNumbers/phoneNumber]='312 555-1234'"
        objects = parse_and_query(query)
        for oneObject in objects:
            self.assertTrue(is_term_fact_value(oneObject, "phoneNumbers/phoneNumber@type", "home"))
            self.assertTrue(is_term_fact_value(oneObject, "phoneNumbers/phoneNumber", "312 555-1234"))

        query = "filter: [phoneNumbers/phoneNumber@type]='home' | filter: [phoneNumbers/phoneNumber]='312 555-1234'"
        objects = parse_and_query(query)
        for oneObject in objects:
            self.assertTrue(is_term_fact_value(oneObject, "phoneNumbers/phoneNumber@type", "home"))
            self.assertTrue(is_term_fact_value(oneObject, "phoneNumbers/phoneNumber", "312 555-1234"))

        query = "filter: [phoneNumbers/phoneNumber@type]='home' | exclude: [phoneNumbers/phoneNumber]='312 555-1234'"
        objects = parse_and_query(query)
        for oneObject in objects:
            self.assertTrue(is_term_fact_value(oneObject, "phoneNumbers/phoneNumber@type", "home"))
            self.assertFalse(is_term_fact_value(oneObject, "phoneNumbers/phoneNumber", "312 555-1234"))

    #@skip
    def test_marked_by(self):
        print_test_name()

        query = "marked_by: (filter: [.*TLP.*] contains 'yellow')"
        objects = parse_and_query(query)
        for oneObject in objects:
            for marking in oneObject.marking_thru.all():
                self.assertTrue(is_term_fact_value(marking.marking, '.*TLP.*', 'yellow'))

        query = "marked_by: (filter: [.*] contains 'yellow' | exclude: [.*] contains 'organization3')"
        objects = parse_and_query(query)
        for oneObject in objects:
            for marking in oneObject.marking_thru.all():
                self.assertTrue(is_term_fact_value(marking.marking, '.*', 'yellow'))
                self.assertFalse(is_term_fact_value(marking.marking, '.*', 'organization3'))

        query = "[lastName] contains 'Mustermann' | marked_by: (filter: [.*TLP.*] contains 'yellow')"
        objects = parse_and_query(query)
        for oneObject in objects:
            self.assertTrue(is_term_fact_value(oneObject, "lastName", "Mustermann", lambda a, b: a in b))
            for marking in oneObject.marking_thru.all():
                self.assertTrue(is_term_fact_value(marking.marking, '.*TLP.*', 'yellow', lambda a, b: a in b))

    #@skip
    def test_not_marked_by(self):
        print_test_name()

        query = "identifier__namespace__uri contains 'test.org' | !marked_by: (filter: [.*TLP.*] contains 'yellow')"
        objects = parse_and_query(query)
        for oneObject in objects:
            self.assertTrue('test.org' in oneObject.identifier.namespace.uri)
            for marking in oneObject.marking_thru.all():
                self.assertFalse(is_term_fact_value(marking.marking, '.*TLP.*', 'yellow'))

        query = "!marked_by: (filter: [.*] contains 'yellow' | exclude: [.*] contains 'organization3')" \
                " | identifier__namespace__uri contains 'test.org'"
        objects = parse_and_query(query)
        for oneObject in objects:
            self.assertTrue('test.org' in oneObject.identifier.namespace.uri)
            for marking in oneObject.marking_thru.all():
                if is_term_fact_value(marking.marking, '.*', 'yellow'):
                    self.assertTrue(is_term_fact_value(marking.marking, '.*', 'organization3'))
                else:
                    self.assertFalse(is_term_fact_value(marking.marking, '.*', 'organization3'))

        query = "[lastName] !contains 'Mustermann' | !marked_by: (filter: [.*TLP.*] contains 'yellow')"
        objects = parse_and_query(query)
        for oneObject in objects:
            self.assertFalse(is_term_fact_value(oneObject, "lastName", "Mustermann", lambda a, b: a in b))
            for marking in oneObject.marking_thru.all():
                self.assertFalse(is_term_fact_value(marking.marking, '.*TLP.*', 'yellow', lambda a, b: a in b))

    #@skip
    def test_not(self):
        print_test_name()

        # Test field
        query = "identifier__uid != 'john_smith'"
        objects = parse_and_query(query)
        for oneObject in objects:
            self.assertNotEqual(oneObject.identifier.uid, "john_smith")

        # Test fact term
        query = "[lastName] != 'Smith'"
        objects = parse_and_query(query)
        for oneObject in objects:
            self.assertFalse(is_term_fact_value(oneObject, "lastName", "Smith"))

        # Test fact term
        query = "[lastName] !icontains 'mIT'"
        objects = parse_and_query(query)
        for oneObject in objects:
            comp = lambda a, b: a.upper() in b.upper()
            self.assertFalse(is_term_fact_value(oneObject, "lastName", "mIT", comp))

        # Test query with boolean operator
        query = "[lastName]!='Smith' && [lastName]='Doe'"
        objects = parse_and_query(query)
        for oneObject in objects:
            self.assertTrue(is_term_fact_value(oneObject, "lastName", "Doe"))

        # Test query with boolean operator
        query = "[lastName]!='Smith' && [lastName]!='Doe'"
        objects = parse_and_query(query)
        for oneObject in objects:
            self.assertFalse(is_term_fact_value(oneObject, "lastName", "Smith"))
            self.assertFalse(is_term_fact_value(oneObject, "lastName", "Doe"))


def parse_and_query(query):
    print ""

    # Parse query
    parser = QueryParser()
    print "\tQuery: %s" % query

    # Generate and execute query
    filter_collection = parser.parse(str(query))
    objects = getattr(InfoObject, 'objects').exclude(latest_of=None)
    objects = filter_collection.build_query(base=objects)
    objects = objects.distinct()
    #print "\tSQL: %s" % objects.query

    return objects


def is_term_fact_value(one_object, fact_term, fact_value, fact_comp=lambda a, b: a == b):
    for fact in one_object.facts.all():
        # One of the fact terms has to be the right one
        if re.match(fact_term, str(fact.fact_term), flags=re.I):
            # One of the values has to be the right one
            for value in fact.fact_values.all():
                #if str(value) == fact_value:
                if fact_comp(fact_value, str(value)):
                    return True
    return False


def print_test_name():
    import traceback
    print "\n======================================\nTest method: %s\n======================================" %\
          traceback.extract_stack(None, 2)[0][2]
