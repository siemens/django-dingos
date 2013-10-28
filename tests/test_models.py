#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_django-dingos
------------

Tests for `django-dingos` modules module.
"""

import unittest

from dingos import models

from utils import deltaCalc

from django import test

from dingos.management.commands.dingo_generic_xml_import import Command

import pprint

pp = pprint.PrettyPrinter(indent=2)

class creation_Tests(test.TestCase):
    def setUp(self):
        pass
    def test_creation(self):

        @deltaCalc
        def tested(*args,**kwargs):
            return models.get_or_create_iobject(*args,**kwargs)

        (delta,result) = tested(identifier_uid="1234",
                                identifier_namespace_uri="http://test.org",
                                iobject_type_name="File",
                                iobject_type_namespace_uri="http://test.org",
                                iobject_type_revision_name='2',
                                iobject_family_name="CybOX",
                                iobject_family_revision_name="2.0")


        expected = [ ('DataTypeNameSpace', 1),
                     ('Identifier', 1),
                     ('IdentifierNameSpace', 1),
                     ('InfoObject', 1),
                     ('InfoObjectFamily', 1),
                     ('InfoObjectType', 1),
                     ('Revision', 2)]

        self.assertEqual(delta,expected)


class InfoObject_Tests(test.TestCase):

    def setUp(self):

        self.enrichment, created = models.get_or_create_iobject(identifier_uid="1234",
                                                         identifier_namespace_uri="http://test.org",
                                                         iobject_type_name="File",
                                                         iobject_type_namespace_uri="http://test.org",
                                                         iobject_type_revision_name='2',
                                                         iobject_family_name="CybOX",
                                                         iobject_family_revision_name="2.0")


    def test_add_fact(self):

        @deltaCalc
        def t_add_fact(*args,**kwargs):
            return self.enrichment.add_fact(*args,**kwargs)


        (delta,result) = t_add_fact(fact_term_name='Filename',
                                    fact_term_attribute=None,
                                    fact_dt_name='String',
                                    fact_dt_kind = models.FactDataType.VOCAB_SINGLE,
                                    values=["iexplore.exe"],
                                    node_id_name='1.0.1')
        #pp.pprint(delta)

        expected = [ ('DataTypeNameSpace', 1),
                     ('Fact', 1),
                     ('FactDataType', 1),
                     ('FactTerm', 1),
                     ('FactTerm2Type', 1),
                     ('FactValue', 1),
                     ('InfoObject2Fact', 1),
                     ('NodeID', 1)]
        self.assertEqual(delta,expected)

        (delta,result) = t_add_fact(fact_term_name='Filename',
                                    fact_term_attribute=None,
                                    fact_dt_name='String',
                                    fact_dt_kind = models.FactDataType.VOCAB_SINGLE,
                                    values=["iexplore.exe","evil.exe"],
                                    node_id_name='2.0.1')
        #pp.pprint(delta)
        self.assertEqual(delta,[('Fact', 1), ('FactValue', 1),('InfoObject2Fact', 1),  ('NodeID', 1)])

        (delta,result) = t_add_fact(fact_term_name='Filename',
                                    fact_term_attribute=None,
                                    fact_dt_name='String',
                                    fact_dt_kind = models.FactDataType.VOCAB_SINGLE,
                                    values=["evil.exe"],
                                    node_id_name='3.0.1')
        #pp.pprint(delta)
        self.assertEqual(delta,[('Fact', 1), ('InfoObject2Fact', 1),  ('NodeID', 1)])

        (delta,result) = t_add_fact(fact_term_name='OtherTerm',
                                    fact_term_attribute=None,
                                    fact_dt_name='String',
                                    fact_dt_kind = models.FactDataType.VOCAB_SINGLE,
                                    values=["evil.exe"],
                                    node_id_name='4.0.1')
        #pp.pprint(delta)
        self.assertEqual(delta,[
                                 ('Fact', 1),
                                 ('FactTerm', 1),
                                 ('FactTerm2Type', 1),
                                 ('InfoObject2Fact', 1),
                                 ('NodeID', 1)])


class XML_Import_Tests(test.TestCase):

    def setUp(self):
        self.command = Command()

    def test_import(self):

        @deltaCalc
        def t_import(*args,**kwargs):
            return self.command.handle(*args,**kwargs)


        (delta,result) = t_import('tests/testdata/xml/person.xml',
                                  uid='youhou',
                                  placeholder_fillers=[],
                                  identifier_ns_uri=None,
                                  marking_json='tests/testdata/markings/import_info.json')
        print "Import Test"
        pp.pprint(delta)

        expected = [ ('DataTypeNameSpace', 2),
                     ('Fact', 17),
                     ('FactDataType', 1),
                     ('FactTerm', 15),
                     ('FactTerm2Type', 15),
                     ('FactValue', 17),
                     ('Identifier', 2),
                     ('IdentifierNameSpace', 1),
                     ('InfoObject', 2),
                     ('InfoObject2Fact', 17),
                     ('InfoObjectFamily', 2),
                     ('InfoObjectType', 2),
                     ('Marking2X', 1),
                     ('NodeID', 16),
                     ('Revision', 2)]

        self.assertEqual(delta,expected)

        (delta,result) = t_import('tests/testdata/xml/person.xml',
                                  uid='youhou',
                                  placeholder_fillers=[],
                                  identifier_ns_uri=None,
                                  marking_json='tests/testdata/markings/import_info.json')
        print "Import Test"

        expected = [ ('Identifier', 1),
                     ('InfoObject', 2),
                     ('InfoObject2Fact', 17),
                     ('Marking2X', 1)]

        self.assertEqual(delta,expected)

        pp.pprint(delta)

