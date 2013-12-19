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



import logging
import pprint
import re
import hashlib
import base64


from django.db import models
from django.db.models import Count, F
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core import urlresolvers
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.core.files.base import ContentFile

import dingos.read_settings

import dingos

from dingos import *

from dingos.core.datastructures import DingoObjDict,ExtendedSortedDict

logger = logging.getLogger(__name__)
pp = pprint.PrettyPrinter(indent=2)

dingos_class_map = {}




RE_SEARCH_PLACEHOLDERS = re.compile(r"\[(?P<bla>[^\]]+)\]")


class DingoModel(models.Model):
    """
    This base class for all dingos models is used to provide all model classes
    with a dictionary of class definitions. The idea is that instead of
    using::

         SomeClass.objects.get_or_create(...)/filter(...)/...

    to access an instance, we use::

         self._DCM['SomeClass'].objects.get_or_create(...)/filter(...)/...

    As long, as we use Dingo proper, this is pointless, but it may be
    helpful when defining abstract classes based on Dingo classes:
    what we want when using abstract classes to always create and work
    with the abstract classes rather than the base Dingo classes.

    This approach does not quite work, because in many cases, instances
    are accessed via the class methods which, by default, always lead
    back to the base Dingo classes. For a while it seemed that this
    could be overcome with Django model managers, but at least until
    Django 1.5, there seems no way to force the usage of a user-defined
    model manager in all cases.

    """

    def __init__(self, *args, **kwargs):
        self._DCM = kwargs.get('dingos_class_map', dingos_class_map)
        try:
            del (kwargs['dingos_class_map'])
        except:
            pass
        models.Model.__init__(self, *args, **kwargs)


    class Meta:
        abstract = True


class FactValue(DingoModel):
    """
    All kind of information eventually boils down to a collection of facts. In DINGO,
    we keep all values of such facts in a single table/model, no matter whether
    the value is something completely unique/specific such as a hash value
    or belongs to a predefined data-type of value vocabulary.
    ("Yes" and "No"; "male", "female", "other", ...).

    If the fact value is part of a pre-defined vocabulary, we
    can store also a additional information about the value (title and description).
    the standard use case for this is to provide a human-readable value and
    help text for automatically generate forms in which the user can
    provide input (drop-down, radio-buttons, etc.)

    Finally: each fact value belongs to a fact data type. The consequence
    of this is that the same value will appear several times in the
    table if it belongs to several data types (e.g., "Yes" may be
    part of a datatype providing for Yes/No information, another
    datatype that allows additionally for a 'Maybe' value, and
    part of a simple "String" datatype where "Yes" happens to
    be the value of a fact expressed as a string. For the
    same datatype, unique values are enforced.

    The default fact data type of a fact value (unless specified
    otherwise) is the "String" datatype belonging to the Dingo default
    namespace.
    """

    value = models.TextField()
    title = models.CharField(max_length=256,
                             blank=True,
                             help_text="""A human-readable version of the value; useful for values
                                          that are part of standard vocabularies.""")
    description = models.TextField(blank=True,
                                   help_text="""A helptext/description of the value; useful for values that
                                                are part of standard vocabularies""")

    fact_data_type = models.ForeignKey("FactDataType",
                                       related_name = 'fact_value_set')




    storage_location = models.SmallIntegerField(choices=((dingos.DINGOS_VALUES_TABLE, "in FactValues table"),
                                                         (dingos.DINGOS_FILE_SYSTEM, "in Filesystem"),
                                                         (dingos.DINGOS_BLOB_TABLE, "in BLOB table" )),
                                                default=dingos.DINGOS_VALUES_TABLE,
                                                help_text="""Governs storage location of value""")


    class Meta:
        # The constraint below can cause problems if the entries in FactValue become to large:
        # Uniqueness forces the creation of a index on values
        # for testing uniqueness.
        unique_together = ('value', 'fact_data_type','storage_location')

    def __unicode__(self):
        return ("%s" % self.value)


dingos_class_map["FactValue"] = FactValue


class FactDataType(DingoModel):
    """
    Each fact value belongs to a fact data type. Fact data types
    are organized in name spaces -- a fact data type of a given
    name can only exist once in a given name space.
    """

    name = models.CharField(max_length=128,
                            help_text="Identifier for data type")

    description = models.TextField(blank=True)

    namespace = models.ForeignKey("DataTypeNameSpace",
                                  related_name = 'fact_data_type_set')

    class Meta:
        unique_together = ('name', 'namespace',)

    UNKNOWN_KIND = 0
    NO_VOCAB = 1
    VOCAB_SINGLE = 2
    VOCAB_MULTIPLE = 3
    REFERENCE = 4

    DATATYPE_KIND = ((UNKNOWN_KIND, "Unknown"),
                     (NO_VOCAB, "Not vocabulary!!"),
                     (VOCAB_SINGLE, "Vocabulary value (single choice)"),
                     (VOCAB_MULTIPLE, "Vocabulary value (multiple choice)"),
                     (REFERENCE, "Reference to InfoObject"),
    )

    kind = models.SmallIntegerField(choices=DATATYPE_KIND,
                                    default=UNKNOWN_KIND,
                                    help_text="""Governs, kind of data type.""")

    @staticmethod
    def autocomplete_search_fields():
        """ This is necessary for the autocomplete field offered by the Grappelli skin."""
        return ("name__icontains",)

    def __unicode__(self):
        ns_name = self.namespace.name
        if ns_name:
            return "%s (%s)" % (self.name, ns_name)
        else:
            return "%s" % self.name


dingos_class_map["FactDataType"] = FactDataType


class DataTypeNameSpace(DingoModel):
    """
    Fact data types are qualified by a namespace, allowing fact data types
    of the same name existing in parallel for different name spaces.

    We also use namespaces to denote owners/sources of information objects
    by giving objects an identifier consisting of a pair of (1) namespace
    of owner/source and (2) unique identifier. This follows the usage
    of "qualified names" as defined in the CybOx/STIX standards.
    """

    uri = models.URLField(max_length=255,
                          unique=True,
                          help_text="URI of namespace. Example: 'http://stix.mitre.org/default_vocabularies-1'")

    name = models.SlugField(max_length=50,
                            blank=True,
                            help_text="""Name of namespace. Example: 'cyboxVocabs'. This name may be used
                                         in XML output to denote the namespace. Note, however, that
                                         the defining characteristic of a namespace is the URI, not the
                                         name: the name is completely exchangeable.""")

    description = models.TextField(blank=True)

    def __unicode__(self):
        if self.name:
            return "%s (%s)" % (self.name, self.uri)
        else:
            return self.uri

    @staticmethod
    def autocomplete_search_fields():
        """ This is necessary for the autocomplete field offered by the Grappelli skin.
            See the Grappelli documenatation for details. """
        return ("name__icontains", "uri__icontains",)


dingos_class_map["DataTypeNameSpace"] = DataTypeNameSpace


class IdentifierNameSpace(DingoModel):
    """
    We use namespaces to denote owners/sources of information objects
    by giving objects an identifier consisting of a pair of (1) namespace
    of owner/source and (2) unique identifier. This follows the usage
    of "qualified names" as defined in the CybOx/STIX standards.
    """

    uri = models.URLField(max_length=255,
                          unique=True,
                          help_text="URI of namespace. Example: 'http://stix.mitre.org/default_vocabularies-1'")

    name = models.SlugField(max_length=50,
                            blank=True,
                            help_text="""Name of namespace. Example: 'my_organization'. This name may be used
                                         in XML output to denote the namespace. Note, however, that
                                         the defining characteristic of a namespace is the URI, not the
                                         name: the name is completely exchangeable.""")

    description = models.TextField(blank=True)

    def __unicode__(self):
        if self.name:
            return "%s (%s)" % (self.name, self.uri)
        else:
            return self.uri

    @staticmethod
    def autocomplete_search_fields():
        """ This is necessary for the autocomplete field offered by the Grappelli skin.
            See the Grappelli documenatation for details. """
        return ("name__icontains", "uri__icontains",)


dingos_class_map["IdentifierNameSpace"] = IdentifierNameSpace



class FactTerm(DingoModel):
    """
    Facts of any kind are essentially key-value pairs such
    as "First Name : Peter", "Gender: Male", etc. In Dingo,
    the values are managed with the FactValue model, whereas
    the keys are managed with the FactTerm model.

    We can provide structure to FactTerms by denoting
    them as "paths", e.g. "Person/Name/First", "Person/Name/Last",
    etc. In the case of XML import, we also treat attributes
    as fact terms: this is printed, e.g., as "Person@gender",
    but within the database, the attribute part of a FactTerm
    (if any) is stored in its own field.

    Here is an example of how we draw fact terms from
    XML documents. Consider the following piece of CybOx 1.0 XML::

        <FileObj:FileObjectType>
           <FileObj:File_Name datatype="String" condition="Equals">UNITED NATIONS COMPENSATION SCHEME...pdf
           </FileObj:File_Name>
           <FileObj:Hashes>
               <Common:Hash>
                   <Common:Type datatype="String">SHA256</Common:Type>
                   <Common:Simple_Hash_Value datatype="hexBinary" condition="Equals">
                   586fea79dd23a352a14c3f8bf3dbc9eb732e1d54f804a29160894aec55df4bd5
                   </Common:Simple_Hash_Value>
               </Common:Hash>
               <Common:Hash>
                   <Common:Type datatype="String">MD5</Common:Type>
                   <Common:Simple_Hash_Value datatype="hexBinary" condition="Equals">
                   471809c2092cecd633e43d465409a78c
                   </Common:Simple_Hash_Value>
               </Common:Hash>
           </FileObj:Hashes>
       </FileObj:FileObjectType>

    This gives rise to the following fact terms (the attributes regarding
    'datatype' are removed by the import, because we track this information
    in the FactDataType).

    - File_Name
    - File_Name@condition
    - Hashes/Hash/Type
    - Hashes/Hash/Simple_Hash_Value
    - Hashes/Hash/Simple_Hash_Value@condition


    By flattening the XML structure out into such fact terms, we would
    loose structural information, but we also keep
    track of tree structure information as we shall see later.

    The fact term model contains relatively little information.
    That  is, because the real information is contained in the "FactTerm2Type"
    model, that ties together FactTerms with all type information
    (FactDataType, InfoObjectFamily and InfoObjectType).
    """

    term = models.CharField(max_length=512,
                            help_text="""A path-like string such as "Header/Subject"
                                           or "Hashes/Hash/Simple_Hash_Value" """,
                            )

    attribute = models.CharField(max_length=128,
                                 help_text="""The key of an (XML) attribute that is part of the fact term (may be empty)""",
                                 )


    @staticmethod
    def autocomplete_search_fields():
        """ This is necessary for the autocomplete field offered by the Grappelli skin;
            it says that autocompletion is done on the 'term' field and checks whether
            what has been typed by the user appears anywhere in a known fact term
            (rather than, e.g., only completing terms that start with what the user has typed.)
            Do not forget to add the '@staticmethod' tag for this function if using
            the same trick for other models."""
        return ("term__icontains","attribute__icontains")

    def __unicode__(self):
        if self.attribute:
            return "%s@%s" % (self.term, self.attribute)
        else:
            return "%s" % self.term

    class Meta:
        unique_together = ('term', 'attribute')


dingos_class_map["FactTerm"] = FactTerm


class InfoObjectNaming(DingoModel):
    """
    DINGO provides a configurable naming system for Information Objects. How
    an Information Object is named is configured by associating it with one
    or more format strings that refer to facts within an object. The first
    format string for which all facts that it refers to are present
    in the format string is used for generating the name of an
    Information Object after import.
    """

    iobject_type = models.ForeignKey("InfoObjectType",
                                     related_name = 'iobject_type_set')
    format_string = models.TextField(help_text="""Format string for naming the information object. The format
                                                  string can refer to fact terms of facts that should be
                                                  present in an Information Object of the given type.""")
    position = models.PositiveSmallIntegerField("Position")

    class Meta:
        ordering = ['position']


dingos_class_map["InfoObjectNaming"] = InfoObjectNaming


class InfoObjectType(DingoModel):
    """
    Dingo organizes information in information objects. Each object
    is assigned an information-object type.

    Examples from the CybOx standard for information-object
    types:

    - File
    - Email
    - NetworkConnection
    - X509Certificate

    """


    name = models.SlugField(max_length=30,
                            help_text="""Name for a type of information object, e.g., 'Email',
                                         'File', 'Relationship', 'InvestigationStep' etc.""")

    description = models.TextField(blank=True)

    iobject_family = models.ForeignKey("InfoObjectFamily",
                                       related_name='iobject_type_set',
                                       help_text='Associated info-object family.')

    namespace = models.ForeignKey("DataTypeNamespace",
                                  blank=True,
                                  related_name='iobject_type_set',
                                  help_text='Namespace of information object type.')


    def __unicode__(self):
        return "%s:%s" % (self.iobject_family,self.name)

    @staticmethod
    def autocomplete_search_fields():
        """
        This is necessary for the autocomplete field offered by the Grappelli skin.
        """
        return ("name__icontains",)

    class Meta:
        unique_together = ('name', 'iobject_family', 'namespace')


dingos_class_map["InfoObjectType"] = InfoObjectType


class InfoObjectFamily(DingoModel):
    """
    There may be several source formats of information objects,
    for example:

    - CybOx
    - STIX
    - OpenIOC
    - ...

    The 'family' associated with an Information Objects informs
    about the source format.
    """

    name = models.SlugField(max_length=256,
                            unique=True,
                            help_text="Identifier for InfoObject Family")

    title = models.CharField(max_length=1024,
                             blank=True,
                             help_text="""A human-readable title for the InfoObject Family""")

    description = models.TextField(blank=True)


    @staticmethod
    def autocomplete_search_fields():
        """ This is necessary for the autocomplete field offered by
            the Grappelli skin."""
        return ("name__icontains",)

    def __unicode__(self):
        return "%s" % self.name


dingos_class_map["InfoObjectFamily"] = InfoObjectFamily


class Revision(DingoModel):
    """
    Both information-object families and information-object types may have
    different revisions (e.g., CybOx 1.0, CybOx 2.0, ...).
    We store revisions in a separate model.
    """
    name = models.CharField(max_length=32,
                            blank=True,
                            unique=True)

    @staticmethod
    def autocomplete_search_fields():
        """ This is necessary for the autocomplete field offered by
            the Grappelli skin."""
        return ("name__icontains",)

    def __unicode__(self):
        return "%s" % self.name


dingos_class_map["Revision"] = Revision


class FactTerm2Type(DingoModel):
    """
    A through model linking FactTerms, InfoObjectTypes and FactDataTypes: it
    specifies the data type of values of the fact term (FactDataType)
    for the given information-object type.

    For example::

       <URIObj:URIObjectType>
           <URIObj:Value datatype="AnyURI" condition="Equals">http://iprice.pl/image.php</URIObj:Value>
       </URIObj:URIObjectType>

    So, in URI-Objects, the fact-term "Value" has datatype "AnyURI". This example
    also shows, why we have to track the data type per object/iobject type:
    it stands to expect that "Value" may occur in other object types and may
    have other data types.
    """

    fact_term = models.ForeignKey("FactTerm",
                                  related_name='iobject_type_thru')

    iobject_type = models.ForeignKey("InfoObjectType",
                                     related_name='fact_term_thru')

    fact_data_types = models.ManyToManyField("FactDataType",
                                             related_name='fact_term_thru')

    title = models.CharField(max_length=1024,
                             blank=True,
                             help_text="""A human-readable title/summary of what the fact term describes for
                                          this InfoObjectType""")
    description = models.TextField(blank=True,
                                   help_text="""A comprehensive description of what the fact-term is used for
                                          in this InfoObjectType.""")

    class Meta:
        unique_together = ('iobject_type', 'fact_term')

    def __unicode__(self):
        return ("%s: %s x %s" % (
            self.iobject_type.iobject_family.name, self.fact_term.term, self.iobject_type.name))


dingos_class_map["FactTerm2Type"] = FactTerm2Type


class NodeID(DingoModel):
    """
    When flattening structured data such as XML files into facts (i.e., combinations
    of fact terms and fact values), we have to keep track of structural information.
    Consider the following example::

          <FileObj:FileObjectType>
           <FileObj:File_Name datatype="String" condition="Equals">UNITED NATIONS COMPENSATION SCHEME...pdf
           </FileObj:File_Name>
           <FileObj:Hashes>
               <Common:Hash>
                   <Common:Type datatype="String">SHA256</Common:Type>
                   <Common:Simple_Hash_Value datatype="hexBinary" condition="Equals">
                   586fea79dd23a352a14c3f8bf3dbc9eb732e1d54f804a29160894aec55df4bd5
                   </Common:Simple_Hash_Value>
               </Common:Hash>
               <Common:Hash>
                   <Common:Type datatype="String">MD5</Common:Type>
                   <Common:Simple_Hash_Value datatype="hexBinary" condition="Equals">
                   471809c2092cecd633e43d465409a78c
                   </Common:Simple_Hash_Value>
               </Common:Hash>
           </FileObj:Hashes>
       </FileObj:FileObjectType>

    This gives rise to the following node identifiers and associated facts,
    denoted in the following list by their fact terms:

    - 'N000': File_Name
    - 'N001:L000:N000' : Hashes/Hash/Type
    - 'N001:L000:N001': Hashes/Hash/Simple_Hash_Value
    - 'N001:L000:N001:A000' :Hashes/Hash/Simple_Hash_Value@condition
    - 'N001:L001:N000' : Hashes/Hash/Type
    - ...

    (The attributes 'datatype' are not considered, because that information is
    consumed during import for calculating datatype information and not duplicated
    in the information object's facts)


    The overall principle should be clear, but two special cases probably require
    additional explanation:

    - Lists such as the list of hash values, in which the same element name 'Hash'
      is repeated several times, are denoted with a 'L' in the node identifier.

    - Attributes are marked with a 'A' (we chose 'A' rather than '@' because then
      the lexicographic ordering on node identifier places attribute facts before
      the children of a node rather than behind the children.

    """
    name = models.CharField(max_length=255,
                            unique=True)

    def __unicode__(self):
        return "%s" % self.name


dingos_class_map["NodeID"] = NodeID


class InfoObject2Fact(DingoModel):
    """
    The model used for linking information objects and facts.
    It is a 'through' model which contains the following
    additional information:

    - node identifier: at which position does the fact
      occur in the information object?

    - if the fact is an attribute and their exists
      a fact to which this fact serves as attribute:
      a pointer to the latter.

      Note that there may be no such fact for an attribute.
      Consider the following example::

        <Cupboard>
          <Drawer items='2'>
            <Item color='silver'>Fork</Item>
            <Item color='black'>Knife></Item>
          </Drawer>
        </Cupboard>

      This is transformed into the following facts
      (with associated node identifier)

      - N000:N001:A000: Cupboard/Drawer@items = 2
      - N000:N001:L000: Cupboard/Drawer/Item = Fork
      - N000:N001:L000:A000 Cupboard/Drawer/Item@color = silver
      - N000:N001:L001: Cupboard/Drawer/Item = Knife
      - N000:N001:L001:A000 Cupboard/Drawer/Item@color = black

      Here, for the fact with node id 'N000:N001:A000' there
      is no associated fact to which '2' is the attribute with
      key 'items': we have no fact 'Cupboard/Drawer', because
      we have flattened the tree into facts and 'Cupboard/Drawer'
      itself is not associated with a value but provides
      hierarchical information.

      For the color attributes 'Cupboards/Drawer/Item@color',
      however, there exist the two facts 'Cupboards/Drawer/Item'
      and DINGO will fill in the information in 'attributed_fact'.

      Note that the reverse relation of 'attributed_fact'
      is named 'attributes', i.e., for the fact within an
      Information Object, you can see whether it has a direct
      attribute.

    """

    iobject = models.ForeignKey("InfoObject",
                                related_name="fact_thru",
                                )

    fact = models.ForeignKey("Fact",
                             related_name="iobject_thru",
                             )

    attributed_fact = models.ForeignKey("InfoObject2Fact",
                                        null=True,
                                        related_name="attributes")

    node_id = models.ForeignKey("NodeID")



    @property
    def marking_thru(self):
        """
        Return the back-pointer to  markings that
        may have been attached via Django's content type mechanism.
        """
        self_django_type = ContentType.objects.get_for_model(self)
        return Marking2X.objects.filter(content_type__pk=self_django_type.id,
                                        object_id=self.id)


    def __unicode__(self):
        return self.fact.fact_term.attribute

    class Meta:
        # This ordering is crucial for proper display of facts
        # in the detail view of an Information Object
        ordering = ['node_id__name']


dingos_class_map["InfoObject2Fact"] = InfoObject2Fact


class Fact(DingoModel):
    """
    In facts, we associate fact terms with one or more fact values.

    A fact may contain a (single) reference to another
    information object. Note that the reference occurs via the
    identifier rather than the information object directly: the semantics
    is that always the latest revision is referred to. If the reference
    to a specific revision is required, the time stamp of that
    revision must also be specified.

    Note that facts do not have a direct foreign key
    relationship with information objects: we link
    information objects and facts via a thru model,
    namely InfoObject2Fact.
    """

    fact_term = models.ForeignKey(FactTerm,
                                  help_text="Pointer to fact term described by this fact.",
                                  )
    fact_values = models.ManyToManyField("FactValue",
                                         null=True,
                                         help_text="""Value(s) of that fact""")

    value_iobject_id = models.ForeignKey("Identifier",
                                         related_name="value_of_set",
                                         null=True,
                                         blank=True,
                                         help_text="""As alternative to a text-based value stored in a fact,
                                                       an iobject can be linked. In this case, there should
                                                       be no fact values associated with the fact.""")

    value_iobject_ts = models.DateTimeField(null=True,
                                            help_text="""Used to reference a specific revision of an information
                                                         object rather than the latest revision.""")


    class Meta:
        # Here, we cannot have database-enforced uniqueness, because we need
        # uniqueness regarding also M2M-related objects, namely the fact values.
        # Refer to the code in get_or_create_fact that shows how to query whether
        # such a fact may already exist.
        pass

    def __unicode__(self):
        fact_values = self.fact_values.all()
        if fact_values.count() > 1:
            more_values = "(%s more values)" % (fact_values.count()-1)
        else:
            more_values = ""
        if len(fact_values[0].value)>50:
            longer = "..."
        else:
            longer = ''
        return "%s: %s%s %s" % (self.fact_term.term, self.fact_values.all()[0].value[0:50],longer,more_values)


    @staticmethod
    def autocomplete_search_fields():
        """ This is necessary for the autocomplete field offered by the Grappelli skin."""
        return ("fact_term__name__icontains",)


dingos_class_map["Fact"] = Fact


class InfoObject(DingoModel):
    """
    So this is the heart of Dingo, the information object class:

    an information object is of a certain type and belongs to
    a certain family. To give examples from CybOx: the type may
    be 'File' and the family is, well, CybOx. For both
    type and class, we may also record a revision (e.g.
    file object of definition "1_2" and family CybOx 2.0).

    An information object contains information via a mapping
    from the information object to facts.

    An information object is marked with an identifier
    and a timestamp. For the same identifier there may be
    several timestamps, thus recording different versions
    of the information object. The newest version of
    an information object can always be found via
    the identifier model: 'self.identifier.latest' always
    points to the latest version.

    If a given information object represents the latest
    revision, the method 'latest_of' (provided as
    reverse relation-ship from the Identifier model)
    is not None but contains 'self' as only element.

    An information object has a name, which is derived
    from the facts contained in the object: the definition
    of how to derive this name is contained in the
    field 'naming_scheme' of the information-object type
    to which the information object belongs. In the interest
    of efficiency when displaying lists of objects,
    the name is not calculated on the fly but should
    be calculated and stored after the information object
    has been created or updated.
    """

    identifier = models.ForeignKey("Identifier",
                                   related_name = 'iobject_set'
                                  )

    timestamp = models.DateTimeField()

    create_timestamp = models.DateTimeField()

    facts = models.ManyToManyField("Fact",
                                   through="InfoObject2Fact",
                                   help_text="Facts that are content of this enrichment")

    iobject_type = models.ForeignKey(InfoObjectType,
                                     related_name = 'iobject_set',
                                     help_text="Each enrichment has an information object type.")

    iobject_type_revision = models.ForeignKey(Revision,
                                              help_text="Each enrichment has an information object type.",
                                              related_name="+")

    iobject_family = models.ForeignKey("InfoObjectFamily",
                                       related_name = 'iobject_set',
                                       help_text="Type of enrichment, e.g. 'CYBOX'")

    iobject_family_revision = models.ForeignKey("Revision",
                                                help_text="Revision of enrichment type , e.g. '1.0'",
                                                related_name='+')
    uri = models.URLField(blank=True,
                          help_text="""URI pointing to further
                                       information concerning this
                                       enrichment, e.g., the HTML
                                       report of a malware analysis
                                       through Cuckoo or similar.""")

    name = models.CharField(max_length=255,
                            blank=True,
                            default='Unnamed',
                            editable=False,
                            help_text="""Name of the information object, usually auto generated.
                                         from type and facts flagged as 'naming'.""")

    @property
    def marking_thru(self):
        """
        Return the back-pointer to a marking that may
        has been attached via Django's content type mechanism.
        """

        self_django_type = ContentType.objects.get_for_model(self)
        return Marking2X.objects.filter(content_type__pk=self_django_type.id,
                                        object_id=self.id)


    class Meta:
        unique_together = (('identifier', 'timestamp'),)
        ordering = ['-timestamp']


    def __unicode__(self):
        return "%s: %s" % (self.iobject_type, self.name)

    def is_empty(self):
        """
        Returns true if the enrichment is empty

        :return:
        """

        return self.fact_thru.count() == 0

    @property
    def embedded_in(self):
        """
        Used in the view for the InfoObject (in order to be able to use the standard class-based object view.
        Should be removed from here and put into a proper custom view for the object.

        This query only returns embedding objects of the latest revision: to change
        this, the filter 'iobject__timestamp=F('iobject__identifier__latest__timestamp' must
        be removed.
        """

        return self._DCM['InfoObject2Fact']. \
            objects. \
            filter(fact__value_iobject_id=self.identifier). \
            filter(iobject__timestamp=F('iobject__identifier__latest__timestamp')). \
            order_by('-iobject__timestamp') \
            .values_list(
            'iobject',
            'iobject__identifier__namespace__uri',
            'iobject__identifier__uid',
            'iobject__timestamp',
            'iobject__name',
            'fact__value_iobject_ts',
            'fact__fact_term__term', 
            'node_id__name').distinct()

    def add_fact(self,
                 fact_term_name,
                 fact_term_attribute,
                 fact_dt_name='String',
                 fact_dt_namespace_name=None,
                 fact_dt_namespace_uri=DINGOS_NAMESPACE_URI,
                 fact_dt_kind=FactDataType.UNKNOWN_KIND,
                 values=None,
                 value_iobject_id=None,
                 value_iobject_ts=None,
                 node_id_name='',
                 is_attribute=False):
        """
        Add a fact to the iobject. If a fact term for the iobject type
        with the given fact data type and source (CYBOX, etc.) does not
        exist yet, it is created.

        """

        if not values:
            values = []

        # get or create fact_term
        fact_term, created = get_or_create_fact_term(iobject_family_name=self.iobject_family.name,
                                                     fact_term_name=fact_term_name,
                                                     fact_term_attribute=fact_term_attribute,
                                                     iobject_type_name=self.iobject_type.name,
                                                     iobject_type_namespace_uri=self.iobject_type.namespace.uri,
                                                     fact_dt_name=fact_dt_name,
                                                     fact_dt_kind=fact_dt_kind,
                                                     fact_dt_namespace_name=fact_dt_namespace_name,
                                                     fact_dt_namespace_uri=fact_dt_namespace_uri,
                                                     dingos_class_map=self._DCM)


        # get or create fact object

        fact_obj, created = get_or_create_fact(fact_term,
                                               fact_dt_name=fact_dt_name,
                                               fact_dt_namespace_uri=fact_dt_namespace_uri,
                                               values=values,
                                               value_iobject_id=value_iobject_id,
                                               value_iobject_ts=value_iobject_ts,
                                               )


        # get or create node identifier

        node_id, created = dingos_class_map['NodeID'].objects.get_or_create(name=node_id_name)

        # If this is an attribute: determine whether there is a fact for which this fact is
        # an attribute.

        node_id_name_components = node_id_name.split(':')

        attributed_io2f = None
        if node_id_name_components[-1] and node_id_name_components[-1][0] == 'A':
            attributed_node_id_name = ":".join(node_id_name_components[:-1])

            try:
                attributed_io2f = dingos_class_map['InfoObject2Fact'].objects.get(iobject=self,
                                                                                 node_id__name=attributed_node_id_name)
            except InfoObject2Fact.DoesNotExist:
                pass

        e2f = self._DCM['InfoObject2Fact'].objects.create(
            node_id=node_id,
            iobject=self,
            fact=fact_obj,
            attributed_fact=attributed_io2f)

        return e2f

    def from_dict(self,
                  dingos_obj_dict,
                  config_hooks=None,
                  namespace_dict=None,
                  special_ft_handler=None):
        """
        Convert DingoObjDict to facts and associate resulting facts with this information object.
        """


        # Instantiate default parameters

        if not config_hooks:
            config_hooks = {}

        datatype_extractor = config_hooks.get('datatype_extractor', (lambda io, f, i, n, d: False))

        special_ft_handler = config_hooks.get('special_ft_handler', None)

        attr_ignore_predicate = config_hooks.get('attr_ignore_predicate', None)

        force_nonleaf_fact_predicate = config_hooks.get('force_nonleaf_fact_predicate', None)

        if not namespace_dict:
            namespace_dict = {}

        if not self.is_empty():
            logger.error("Attempt to import a dictionary into a non-empty info object")
            return

        # Flatten the DingoObjDict

        (flat_list, attrs) = dingos_obj_dict.flatten(attr_ignore_predicate=attr_ignore_predicate,
                                                     force_nonleaf_fact_predicate=force_nonleaf_fact_predicate)

        for fact in flat_list:

            # Collect the information about all attributes relevant
            # for this node (i.e., they occur either directly on
            # the node or on an ancestor node).

            # The following code was used to generate a attribute dictionary::
            #
            #     attr_info = ExtendedSortedDict()
            #     for attr_node in attrs.keys():
            #         if fact['node_id'].startswith(attr_node):
            #            for (key, value) in attrs[attr_node].items():
            #                attr_info.chained_set(value, 'set', key, attr_node)
            #
            # The dictionary contained full information about also the attributes given
            # to ancestor nodes. So far, we have not required this
            # information for our imports, and thus simplify to a
            # dictionary that only contains the attributes directly
            # associated with the current node.
            #
            # If, at a later stage, we find we need this kind of information,
            # we will can use Django's MultiValueDict to add additional
            # information without changing the signature of the receiving
            # predicate and handler functions.


            attr_info = dict(attrs.get(fact['node_id'],[]))

            #for attr_node in attrs.keys():
            #    if fact['node_id'] == (attr_node):
            #        for (key, value) in attrs[attr_node].items():
            #            attr_info.chained_set(value, 'set', key, attr_node)


            # Fill dictionary with arguments for call to 'add_fact'

            add_fact_kargs = {}
            add_fact_kargs['fact_dt_kind'] = FactDataType.UNKNOWN_KIND
            add_fact_kargs['fact_dt_namespace_name'] = "%s-%s" % (
                self.iobject_family.name, self.iobject_family_revision.name)

            # See whether the datatype extractor has found a datatype for the value

            datatype_found = datatype_extractor(self, fact, attr_info, namespace_dict, add_fact_kargs)

            if not datatype_found:
                add_fact_kargs = {}
                add_fact_kargs['fact_dt_kind'] = FactDataType.NO_VOCAB
                add_fact_kargs['fact_dt_namespace_name'] = DINGOS_NAMESPACE_SLUG
                add_fact_kargs['fact_dt_namespace_uri'] = DINGOS_NAMESPACE_URI
            else:
                # Check whether the datatype extractor added namespace information
                # If not, add some here
                if not 'fact_dt_namespace_uri' in add_fact_kargs:
                    add_fact_kargs['fact_dt_namespace_uri'] = namespace_dict.get(
                        add_fact_kargs['fact_dt_namespace_name'], '%s/%s' % (
                            DINGOS_NAMESPACE_URI, self.iobject_family))

            add_fact_kargs['fact_term_name'] = fact['term']
            add_fact_kargs['fact_term_attribute'] = fact['attribute']
            add_fact_kargs['values'] = [fact['value']]
            add_fact_kargs['node_id_name'] = fact['node_id']

            handler_return_value = True

            logger.debug("Treating fact (before special handler list) %s with attr_info %s and kargs %s" % (fact, attr_info, add_fact_kargs))
            # Below, go through the handlers in the special_ft_handler list --
            # if the predicate returns True for the fact, execute the handler
            # on the fact. If a handler returns False/None, the fact is *not*
            # added. This should only be done, if the handler has added the
            # fact -- otherwise the sequence of node identifiers is messed up!

            if special_ft_handler:
                for (predicate, handler) in special_ft_handler:
                    if predicate(fact, attr_info):
                        handler_return_value = handler(self, fact, attr_info, add_fact_kargs)
                        if not handler_return_value:
                            break
            logger.debug("Treating fact (before special handler list) %s with attr_info %s and kargs %s" % (fact, attr_info, add_fact_kargs))
            if (handler_return_value == True):
                e2f_obj = self.add_fact(**add_fact_kargs)
            elif not handler_return_value:
                continue
            else:
                e2f_obj = handler_return_value
        self.set_name()


    def to_dict(self,include_node_id=False):
        flat_result = []

        fact_thrus = self.fact_thru.all().prefetch_related(
                                                           'fact__fact_term',
                                                           'fact__fact_values',
                                                           'fact__fact_values__fact_data_type',
                                                           'fact__fact_values__fact_data_type__namespace',
                                                           'fact__value_iobject_id',
                                                           'fact__value_iobject_id__namespace',
                                                           'node_id')

        #fact_thrus = self.fact_thru.all()
        for fact_thru in fact_thrus:
            value_list = []
            first = True
            fact_datatype_name = None
            fact_datatype_ns = None
            for fact_value in fact_thru.fact.fact_values.all():
                if first:
                    fact_datatype_name = fact_value.fact_data_type.name
                    fact_datatype_ns = fact_value.fact_data_type.namespace.uri
                    if (fact_datatype_name == DINGOS_DEFAULT_FACT_DATATYPE and
                        fact_datatype_ns == DINGOS_NAMESPACE_URI):

                        fact_datatype_name = None
                        fact_datatype_ns = None
                        first = False
                value_list.append(fact_value.value)

            fact_dict = {'node_id': fact_thru.node_id.name,
                         'term': fact_thru.fact.fact_term.term,
                         'attribute' : fact_thru.fact.fact_term.attribute,
                         '@@type': fact_datatype_name,
                         '@@type_ns': fact_datatype_ns,
                         'value_list': value_list}

            if fact_thru.fact.value_iobject_id:
                value_iobject_id_ns = fact_thru.fact.value_iobject_id.namespace.uri
                value_iobject_id  =fact_thru.fact.value_iobject_id.uid
                fact_dict['@@idref_ns'] = fact_thru.fact.value_iobject_id.namespace.uri
                fact_dict['@@idref_id'] = fact_thru.fact.value_iobject_id.uid
            flat_result.append(fact_dict)

        result = DingoObjDict()
        result.from_flat_repr(flat_result,include_node_id=include_node_id)
        result['@@iobject_type'] = self.iobject_type.name
        result['@@iobject_type_ns'] = self.iobject_type.namespace.uri
        #result = result.to_tuple()
        return result

    def show_fact_terms(self,level):
        """Returns a list of the fact terms (split in 'term' and 'attribute') that
         occur in this InfoObject."""

        fact_terms = self._DCM["FactTerm"].objects.filter(fact__infoobject__pk=self.pk). \
            distinct('term','attribute').values('term','attribute')


        #fact_terms = self._DCM["FactTerm"].objects.filter(fact__iobject_thru__iobject__pk=self.pk).\
        #    filter(fact__iobject_thru__node_id__name__startswith=level).order_by('term','attribute').\
        #    distinct('term','attribute').values_list('fact__iobject_thru__node_id__name','term','attribute')

        return list(fact_terms)

    def extract_name(self):
        """
        We want to dynamically name the iobject based on its type and
        selected facts. This is, what this function does: it collects
        all facts that have "naming" set and concatenates them in the
        order given by the "naming" argument.
        If no fact has such a flag, the type is used

        """
        name = None

        name_schemas = self._DCM["InfoObjectNaming"].objects.filter(iobject_type=self.iobject_type).order_by(
            'position').values_list('format_string', flat=True)

        name_components = []

        # We retrieve all facts of the object

        fact_list = self._DCM['Fact'].objects.filter(iobject_thru__iobject=self).order_by(
            'iobject_thru__node_id__name').values_list('iobject_thru__node_id__name',
                                                        'fact_term__term',
                                                        'fact_term__attribute',
                                                        'fact_values__value',
                                                        'value_iobject_id__latest__name')

        # We build a dictionary that will then be used for the format string

        fact_dict = {}
        counter = 0
        for (node_id, fact_term, attribute, value, related_obj_name) in fact_list:
            #print fact_list[counter]
            if type(value)==type([]):
                value = "%s,..." % value
            if related_obj_name:
                value = related_obj_name

            if attribute:
                fact_term = "%s@%s" % (fact_term, attribute)

            if not fact_term in fact_dict:
                fact_dict[fact_term] = value

            # In addition to the mapping of fact term to (first) value,
            # we add a way to refer to fact terms and values by their
            # node id

            fact_dict["term_of_node_%s" % node_id] = fact_term
            fact_dict["value_of_node_%s" % node_id] = value
            if counter < 10:
                fact_dict["term_of_fact_num_%01d" % counter] = fact_term
                fact_dict["value_of_fact_num_%01d" % counter] = value
            counter += 1
        fact_dict["fact_count_equal_%s?" % counter] = ""
        fact_dict["fact_count"] = "%s" % counter

        name_found = False

        # Now, we go through the format strings and see whether one of them
        # is successfully instantiated via the fact dictionary
        #print fact_dict

        for format_string in name_schemas:
            # Massage the format string such that we can use it as Python format string

            # Escape possible '%'
            format_string = format_string.replace('%','\%')
            # Replace placeholder definitions with python string formatting
            format_string = RE_SEARCH_PLACEHOLDERS.sub("%(\\1)s", format_string)




            try:
                name = format_string % fact_dict
                name_found = True
                break
            except:
                continue

        if not name_found:
            if self.iobject_type.name == 'PLACEHOLDER':
                return "PLACEHOLDER"
            else:
                return "%s (%s facts)" % (self.iobject_type.name,counter)
        else:
            return name

    def set_name(self,name=None):
        """
        Set the name of the object. If no name is given, the
        name is extracted via the extract_name method.
        """
        if name:
            self.name = name[:254]
        else:
            self.name = self.extract_name()[:254]

        self.save()

        return self.name

    def add_relation(self,
                     target_id=None,
                     relation_types=None,
                     fact_dt_namespace_name=None,
                     fact_dt_namespace_uri=DINGOS_NAMESPACE_URI,
                     fact_dt_kind=FactDataType.UNKNOWN_KIND,
                     fact_dt_name='String',
                     metadata_dict=None,
                     markings=None
    ):
        """
        Add a relationship between this object and another object.
        """
        if not markings:
            markings = []

        if relation_types == None:
            relation_types = []

        # Create fact-term for relation types
        relation_type_ft, created = get_or_create_fact_term(iobject_family_name=self.iobject_family.name,
                                                            fact_term_name=DINGOS_RELATION_TYPE_FACTTERM_NAME,
                                                            iobject_type_name=self.iobject_type.name,
                                                            iobject_type_namespace_uri=self.iobject_type.namespace.uri,
                                                            fact_dt_name=fact_dt_name,
                                                            fact_dt_namespace_name=fact_dt_namespace_name,
                                                            fact_dt_kind=fact_dt_kind,
                                                            fact_dt_namespace_uri=fact_dt_namespace_uri)

        # Create fact containing relation types
        relation_type_fact, created = get_or_create_fact(fact_term=relation_type_ft,
                                                         fact_dt_name=fact_dt_name,
                                                         fact_dt_namespace_uri=fact_dt_namespace_uri,
                                                         values=relation_types,
                                                         value_iobject_id=None,
                                                         value_iobject_ts=None,
                                                         )

        rel_target_id = target_id
        rel_source_id = self.identifier

        # Create relation object
        relation, created = self._DCM['Relation'].objects.get_or_create(
            source_id=rel_source_id,
            target_id=rel_target_id,
            relation_type=relation_type_fact)

        # Add markings
        for marking in markings:
            Marking2X.objects.create(marked=relation,
                                     marking=marking)

        if metadata_dict:
            # If the relation already existed and had associated metadata,
            # we retrieve the identifier of that metadata object and
            # write the current metadata as new revision. Otherwise,
            # we create a new identifier.

            if relation.metadata_id:
                rel_identifier_uid = relation.metadata_id.uid
                rel_identifier_namespace_uri = relation.metadata_id.namespace.uri
            else:
                rel_identifier_uid = None
                rel_identifier_namespace_uri = DINGOS_ID_NAMESPACE_URI

            metadata_iobject, created = get_or_create_iobject(identifier_uid=rel_identifier_uid,
                                                              identifier_namespace_uri=rel_identifier_namespace_uri,
                                                              iobject_type_name=DINGOS_RELATION_METADATA_OBJECT_TYPE_NAME,
                                                              iobject_type_namespace_uri=DINGOS_NAMESPACE_URI,
                                                              iobject_type_revision_name=DINGOS_REVISION_NAME,
                                                              iobject_family_name=DINGOS_IOBJECT_FAMILY_NAME,
                                                              iobject_family_revision_name=DINGOS_REVISION_NAME,
                                                              timestamp=None,
                                                              overwrite=False)
            metadata_iobject.from_dict(metadata_dict)

        return relation

    @property
    def view_link(self):
        """
        Return link to Dingo's Detail View for InfoObjects. We use this
        in the Django Admin interface to provide a link to this page
        whenever an information object is shown (e.g., in the InfoObject
        list view).
        """
        iobject_url = urlresolvers.reverse('url.dingos.view.infoobject', args=(self.id,))
        return mark_safe(
            """<a href="%s"><img src="/static/admin/img/selector-search.gif" alt="Lookup" height="16" width="16">""" % iobject_url)


dingos_class_map["InfoObject"] = InfoObject


class Identifier(DingoModel):
    """
    Each information object has an identifier, that consists of a name space,
    denoting the owner/source of an object, and a uid. The 'latest' field
    should always point to the most recent information object of a given
    identifier, i.e., the one with the most recent time stamp.
    """

    uid = models.SlugField(max_length=255)
    namespace = models.ForeignKey("IdentifierNameSpace")

    latest = models.OneToOneField(InfoObject,
                                  null=True, # need this for creation (hen-egg problem)
                                  related_name="latest_of")


    def __unicode__(self):
        return "%s (%s)" % (self.uid, self.namespace.uri)

    class Meta:
        unique_together = ('uid', 'namespace',)


dingos_class_map["Identifier"] = Identifier


class Relation(DingoModel):
    """
    Relations between information objects.

    """

    source_id = models.ForeignKey(Identifier,
                                  null=True,
                                  related_name='yields_via',
                                  help_text="""Pointer to source iobject, i.e., the iobject from
                                               which something was derived""")



    target_id = models.ForeignKey(Identifier,
                                  null=True,
                                  related_name='yielded_by_via',
                                  help_text="Pointer to derived iobject")


    relation_type = models.ForeignKey(Fact,
                                      help_text="Description of nature of relation in direction source to target.")

    metadata_id = models.ForeignKey(Identifier,
                                    null=True,
                                    related_name='+',
                                    help_text="InfoObject containing metadata about relation.")

    @property
    def marking_thru(self):
        """
        Return the back-pointer to markings that may have
        been attached via Django's content type mechanism.
        """

        self_django_type = ContentType.objects.get_for_model(self)
        return Marking2X.objects.filter(content_type__pk=self_django_type.id,
                                        object_id=self.id)


    class Meta:
        unique_together = ("source_id",
                           "target_id",
                           "relation_type")

    def __unicode__(self):
        return "Relation %s" % self.pk


dingos_class_map["Relation"] = Relation

class BlobStorage(models.Model):
    """
    A table for storing large values.
    """

    sha256 = models.CharField(unique=True,
                              max_length=64
                              )

    content = models.TextField(blank=True)


dingos_class_map["BlobStorage"] = BlobStorage

class Marking2X(models.Model):
    """
    Information Objects, single facts within an information object, or Relations
    can be marked with another information object. We use Django's content-type
    mechanism to allow relationships with several models.
    """
    marking = models.ForeignKey(InfoObject,
                                related_name='marked_item_thru')
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    marked = generic.GenericForeignKey('content_type', 'object_id')


dingos_class_map["Marking2X"] = Marking2X


def get_or_create_iobject(identifier_uid,
                          identifier_namespace_uri,
                          iobject_type_name,
                          iobject_type_namespace_uri,
                          iobject_type_revision_name,
                          iobject_family_name,
                          iobject_family_revision_name="",
                          identifier_namespace_name="",
                          timestamp=None,
                          create_timestamp=None,
                          overwrite=False,
                          dingos_class_map=dingos_class_map):
    """
    Get or create an information object.
    """

    # create or retrieve the iobject type and revision

    # create or retrieve identifier

    id_namespace, created = dingos_class_map['IdentifierNameSpace'].objects.get_or_create(uri=identifier_namespace_uri)

    if created and identifier_namespace_name:
        id_namespace.name = identifier_namespace_name
        id_namespace.save()

    identifier, created = dingos_class_map['Identifier'].objects.get_or_create(uid=identifier_uid,
                                                                              namespace=id_namespace,
                                                                              defaults={'latest': None})

    iobject_type_namespace, created = dingos_class_map['DataTypeNameSpace'].objects.get_or_create(uri=iobject_type_namespace_uri)

    iobject_family, created = dingos_class_map['InfoObjectFamily'].objects.get_or_create(name=iobject_family_name)
    iobject_family_revision, created = dingos_class_map['Revision'].objects.get_or_create(
        name=iobject_family_revision_name)

    # create or retrieve the iobject type
    iobject_type, created = dingos_class_map['InfoObjectType'].objects.get_or_create(name=iobject_type_name,
                                                                                    iobject_family=iobject_family,
                                                                                    namespace=iobject_type_namespace)
    iobject_type_revision, created = dingos_class_map['Revision'].objects.get_or_create(name=iobject_type_revision_name)

    if not create_timestamp:
        create_timestamp = timezone.now()
    if not timestamp:
        timestamp = create_timestamp

    if overwrite:
        iobject = overwrite
        created = False


    else:
        iobject, created = dingos_class_map["InfoObject"].objects.get_or_create(identifier=identifier,
                                                                               timestamp=timestamp,
                                                                               defaults={'iobject_family': iobject_family,
                                                                                         'iobject_family_revision': iobject_family_revision,
                                                                                         'iobject_type': iobject_type,
                                                                                         'iobject_type_revision': iobject_type_revision,
                                                                                         'create_timestamp': create_timestamp})
    if created:
        iobject.set_name()
        iobject.save()

    elif overwrite:
        iobject.timestamp = timestamp
        iobject.create_timestamp = create_timestamp
        iobject.iobject_family = iobject_family
        iobject.iobject_family_revision = iobject_family_revision
        iobject.iobject_type = iobject_type
        iobject.iobject_type_revision = iobject_type_revision
        iobject.set_name()
        iobject.save()

    logger.debug(
        "Created iobject with %s (created was %s) and %s (overwrite %s)" % (iobject.identifier, timestamp, created, overwrite))
    return iobject, created


def get_or_create_fact(fact_term,
                       fact_dt_name='String',
                       fact_dt_namespace_uri=DINGOS_NAMESPACE_URI,
                       values=None,
                       value_iobject_id=None,
                       value_iobject_ts=None,
                       ):
    """
    Get or create a fact object.
    """

    if not values:
        values = []


    vocab_namespace, created = dingos_class_map['DataTypeNameSpace'].objects.get_or_create(uri=fact_dt_namespace_uri)

    fact_data_type, created = dingos_class_map['FactDataType'].objects.get_or_create(name=fact_dt_name,
                                                                                    namespace=vocab_namespace)

    # Maybe we already have a fact with exactly the same fact term and the same fact values?
    # We start by looking at the number of values

    value_objects = []

    for value in values:
        storage_location=dingos.DINGOS_VALUES_TABLE
        # collect (create or get) the required value objects
        if value == None:
            value = ''
        if isinstance(value,tuple):
            # If a value is wrapped in a tuple, the second component of the tuple
            # specifies the storage location of the value.
            value, storage_location = value

        if storage_location == dingos.DINGOS_VALUES_TABLE:
            # If the value is larger than a given size, the value is written to disk, instead.
            # We use this to keep too large values out of the database. Depending on how the
            # database is set up, this may be necessary to allow indexing, which in turn is
            # required to check uniqueness on values.

            if len(value) > dingos.DINGOS_MAX_VALUE_SIZE_WRITTEN_TO_VALUE_TABLE:
                (value_hash,storage_location) = write_large_value(value)
                value = value_hash


        fact_value, created = dingos_class_map['FactValue'].objects.get_or_create(value=value,
                                                                                 fact_data_type=fact_data_type,
                                                                                 storage_location=storage_location)
        value_objects.append(fact_value)



    # Do we already have a fact with given fact term and given values?
    #
    # For understanding the query below better, see https://groups.google.com/forum/#!topic/django-users/X9TCSrBn57Y.
    # The double query is necessary, because the first count counts the number of selected
    # fact_value objects, not the number of total objects for each fact.

    matching_facts = Fact.objects.filter(fact_values__in=value_objects). \
        annotate(num_values=Count('fact_values')). \
        filter(num_values=len(value_objects)). \
        filter(value_iobject_id=value_iobject_id). \
        filter(value_iobject_ts=value_iobject_ts). \
        filter(fact_term=fact_term). \
        exclude(id__in= \
        Fact.objects.annotate(total_values=Count('fact_values')). \
            filter(total_values__gt=len(value_objects)))

    created = True
    try:
        fact_obj = matching_facts[0]
        created = False
        logger.debug("FOUND MATCHING OBJECT with pk %s" % fact_obj.pk)
    except:
        fact_obj = dingos_class_map['Fact'].objects.create(fact_term=fact_term,
                                                          value_iobject_id=value_iobject_id,
                                                          value_iobject_ts=value_iobject_ts,
                                                           )

        fact_obj.fact_values.add(*value_objects)
        fact_obj.save()


    return fact_obj, created


def get_or_create_fact_term(iobject_family_name,
                            fact_term_name,
                            fact_term_attribute,
                            iobject_type_name,
                            iobject_type_namespace_uri,
                            fact_dt_name=DINGOS_DEFAULT_FACT_DATATYPE,
                            fact_dt_namespace_name=None,
                            fact_dt_kind=FactDataType.UNKNOWN_KIND,
                            fact_dt_namespace_uri=DINGOS_NAMESPACE_URI,
                            dingos_class_map=dingos_class_map
):
    """
    Get or create a fact term.
    """

    if not fact_term_attribute:
        fact_term_attribute = ''

    # create or retrieve the enrichment type and revision

    iobject_family, created = dingos_class_map['InfoObjectFamily'].objects.get_or_create(name=iobject_family_name)

    # create or retrieve namespace of data type

    fact_dt_namespace, created = dingos_class_map['DataTypeNameSpace'].objects.get_or_create(uri=fact_dt_namespace_uri)

    # create or retrieve namespace of the infoobject type

    iobject_type_namespace, created = dingos_class_map['DataTypeNameSpace'].objects.get_or_create(uri=iobject_type_namespace_uri)

    if created and fact_dt_namespace_name:
        fact_dt_namespace.name = fact_dt_namespace_name
        fact_dt_namespace.save()


    # create or retrieve the fact-value data type object
    fact_dt, created = dingos_class_map['FactDataType'].objects.get_or_create(name=fact_dt_name,
                                                                              namespace=fact_dt_namespace)

    if created:
        fact_dt.kind = fact_dt_kind
        fact_dt.save()

    # create or retreive the iobject type
    iobject_type, created = dingos_class_map['InfoObjectType'].objects.get_or_create(name=iobject_type_name,
                                                                                    iobject_family=iobject_family,
                                                                                    namespace=iobject_type_namespace)

    fact_term, created = dingos_class_map['FactTerm'].objects.get_or_create(term=fact_term_name,
                                                                           attribute=fact_term_attribute)

    fact_term_2_type, dummy = dingos_class_map['FactTerm2Type'].objects.get_or_create(fact_term=fact_term,
                                                                                     iobject_type=iobject_type,
                                                                                     )

    fact_term_2_type.fact_data_types.add(fact_dt)

    fact_term_2_type.save()

    return fact_term, created


def write_large_value(value,storage_location=dingos.DINGOS_LARGE_VALUE_DESTINATION):
    value_hash = hashlib.sha256(value).hexdigest()
    if storage_location == dingos.DINGOS_FILE_SYSTEM:

        file_name = '%s.blob' % (value_hash)

        if dingos.DINGOS_BLOB_STORAGE.exists(file_name):
            dingos.DINGOS_BLOB_STORAGE.delete(file_name)

        dingos.DINGOS_BLOB_STORAGE.save(file_name, ContentFile(value))

    else:
        storage_location = dingos.DINGOS_BLOB_TABLE
        # The blob storage table is default
        dingos_class_map['BlobStorage'].objects.get_or_create(sha256=value_hash,
                                                              content=value)
    return (value_hash,storage_location)

