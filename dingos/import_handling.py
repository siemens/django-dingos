# Copyright (c) Siemens AG, 2013
#
# This file is part of MANTIS.  MANTIS is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
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
import uuid

import libxml2

from collections import deque

from django.utils import timezone

from dingos import *
from dingos.core.datastructures import DingoObjDict
from core.xml_utils import extract_attributes
from dingos.models import dingos_class_map, get_or_create_iobject, Marking2X

import pprint

pp = pprint.PrettyPrinter(indent=2)

logger = logging.getLogger(__name__)



# The constants below are returned by the import function, informing
# about whether an object of the given identifier and timestamp
# already existed.



EXIST_ID_AND_EXACT_TIMESTAMP = "existed"
EXIST_ID_AND_OLDER_TIMESTAMP = "existed_older"
EXIST_ID_AND_NEWER_TIMESTAMP = "existed_newer"
EXIST_PLACEHOLDER = 'exist_placeholder'
NO_EXISTING_OBJECT_FOUND = False


class DingoImportHandling(object):
    def __init__(self, *args, **kwargs):
        logger.debug("Instantiated DingoImportHandling")
        self._DCM = kwargs.get('dingos_class_map', dingos_class_map)
        try:
            del (kwargs['dingos_class_map'])
        except:
            pass


    def get_latest_revision_of_iobject_by_uid(self, namespace_uri, uid):
        """
        Given an information object identifier (represented by uid and uri of the identifier's namespace),
        this function returns the latest revision of an information
        object. If no object of the given identifier exists, None is returned.
        """
        uid_objects = self._DCM['InfoObject'].objects.filter(identifier__namespace__uri=namespace_uri,
                                                             identifier__uid=uid).order_by('-timestamp')

        if uid_objects.count() >= 1:
            return uid_objects[0]
        else:
            return None



    def create_iobject(self,
                       identifier_ns_uri=None,
                       uid=None,
                       timestamp=None,
                       create_timestamp=None,
                       iobject_data=None,
                       config_hooks=None,
                       namespace_dict=None,
                       markings=None,
                       import_older_ts=False,
                       iobject_family_name=DINGOS_IOBJECT_FAMILY_NAME,
                       iobject_family_revision_name=DINGOS_REVISION_NAME,
                       iobject_type_name=DINGOS_PLACEHOLDER_TYPE_NAME,
                       iobject_type_namespace_uri=DINGOS_NAMESPACE_URI,
                       iobject_type_revision_name="",
                       ):
        """
        Create an information object:

        - the unique identifier of the information object is specified
          by identifier_ns_uri and uid

        - the timestamp specifies the revision of the information object

        - iobject data must contain the DingoObjDict with the contents
          of the information object that is to be created

        - config_hooks specifies hooking functions for customizing the
          way the DingoObjDict is transformed into facts -- please
          look at the sample import modules for STIX and OpenIOC to
          get an idea of how this is used

        - A list of markings can be provided. Essentially, a marking is simply
          another information object, to which the created information object
          will receive a link. This can be used, e.g., to keep track of provenance
          information (e.g., which import step led to the creation of that information object.

        - Existing defaults for object family and type can be changed via function parameters.
          If nothing is changed, then a DINGO PLACEHOLDER object is created. This special
          object is used by the importer to create objects for forward references found
          during the import.

        Call the function as
    
        (iobject(s),exists) = create_iobject(...)
    
        The 'exists' flag contains information about whether there were already existing
        revisions.

        """

        # Fill in parameter defaults that would be mutable.

        if not iobject_data:
            iobject_data = DingoObjDict()

        if not config_hooks:
            config_hooks = {}

        existing_iobject = None
        existing_timestamp = None

        exists = False
        overwrite = False

        # Check for existing objects of the given uid
        if uid:
            existing_iobject = self.get_latest_revision_of_iobject_by_uid(identifier_ns_uri, uid)
            if existing_iobject:
                existing_timestamp = existing_iobject.timestamp

        if existing_iobject:

            if existing_iobject.iobject_type.name == DINGOS_PLACEHOLDER_TYPE_NAME \
                and existing_iobject.iobject_family.name == DINGOS_IOBJECT_FAMILY_NAME:

                overwrite = True
                exists = EXIST_PLACEHOLDER



            else:
                # We found a non-Placeholder object; let us see, what the timestamp says.
                existing_timestamps = self._DCM['InfoObject'].objects.filter(identifier__uid=uid).filter(
                    identifier__namespace__uri=identifier_ns_uri).values_list('timestamp', flat=True)
                if timestamp in existing_timestamps:
                    exists = EXIST_ID_AND_EXACT_TIMESTAMP
                elif timestamp < existing_timestamp:
                    exists = EXIST_ID_AND_NEWER_TIMESTAMP
                else:
                    exists = EXIST_ID_AND_OLDER_TIMESTAMP

        # If we have found an object of the given id with the exact timestamp or
        # a newer object and the parameter 'import_older_ts' is set to False,
        # we return the latest revision (i.e., object with newest time stamp) of
        # for the given identifier.


        logger.debug("EXISTS flag for %s:%s is: %s" % (identifier_ns_uri, uid, exists))

        if exists==EXIST_ID_AND_EXACT_TIMESTAMP or (not import_older_ts and exists == EXIST_ID_AND_NEWER_TIMESTAMP):
            return (existing_iobject, exists)

        else:
            # Otherwise, we create the object

            if not uid:
                uid = uuid.uuid1()
            logger.info("Creating %s:%s with timestamp %s" % (identifier_ns_uri,
                                                              uid,
                                                              '{:%d-%m-%Y:%H:%M:%S}.{:03d}'.format(timestamp, timestamp.microsecond // 1000)))
            iobject, created = get_or_create_iobject(uid,
                                                     identifier_ns_uri,
                                                     iobject_type_name,
                                                     iobject_type_namespace_uri,
                                                     iobject_type_revision_name,
                                                     iobject_family_name,
                                                     iobject_family_revision_name,
                                                     identifier_namespace_name=None,
                                                     timestamp=timestamp,
                                                     create_timestamp=create_timestamp,
                                                     overwrite=existing_iobject,
                                                     dingos_class_map=self._DCM,
                                                    )

            # After creating the object, we write the facts to the object.
            # We overwrite in the special case that a PLACEHOLDER was found.

            if created or overwrite:
                iobject.from_dict(iobject_data, config_hooks=config_hooks, namespace_dict=namespace_dict)


            # We adjust the back pointer in the identifier table to the latest version
            # of the object
            if not exists or exists == EXIST_ID_AND_OLDER_TIMESTAMP or exists == EXIST_PLACEHOLDER:
                iobject.identifier.latest = iobject
                iobject.identifier.save()

            if markings:
                # If markings were given, we create the marking.

                for marking in markings:
                    Marking2X.objects.create(marked=iobject,
                                             marking=marking)

            return (iobject, exists)


    def create_marking_iobject(self,
                               uid=None,
                               timestamp=timezone.now(),
                               metadata_dict=None,
                               id_namespace_uri=DINGOS_DEFAULT_ID_NAMESPACE_URI,
                               iobject_family_name=DINGOS_IOBJECT_FAMILY_NAME,
                               iobject_family_revison_name=DINGOS_REVISION_NAME,
                               iobject_type_name=DINGOS_DEFAULT_IMPORT_MARKING_TYPE_NAME,
                               iobject_type_namespace_uri=DINGOS_NAMESPACE_URI,
                               iobject_type_revision_name=DINGOS_REVISION_NAME,
                               ):
        """
        A specialized version of create_iobject with defaults set such that a default marking object is created.
        """
        if not uid:
            uid = uuid.uuid1()

        iobject, created = self.create_iobject(iobject_family_name=iobject_family_name,
                                                      iobject_family_revision_name=iobject_family_revison_name,
                                                      iobject_type_name=iobject_type_name,
                                                      iobject_type_namespace_uri=iobject_type_namespace_uri,
                                                      iobject_type_revision_name=iobject_type_revision_name,
                                                      iobject_data=metadata_dict,
                                                      uid=uid,
                                                      identifier_ns_uri=id_namespace_uri,
                                                      timestamp=timestamp,
                                                      )

        return iobject

    def xml_import(self,
                   xml_fname=None,
                   xml_content=None,
                   ns_mapping=None,
                   embedded_predicate=None,
                   id_and_revision_extractor=None,
                   extract_empty_embedded=False,
                   keep_attrs_in_created_reference=True,
                   transformer=None):
        """
        This is the generic XML import function for dingos. Its parameters
        are as follows:

        - xml_fname: Filename of the XML file to be read
        - xml_content: Alternatively, the xml_content can be provided as string
          or as XMLNode (i.e., a piece of XML that has already been parsed)
        - ns_mapping: A dictionary that may already contain mappings of namespaces
          to namespace URIs. Attention: this dictionary will be enriched with namespace
          information found in the XML file!!!
        - embedded_predicate:
          A function that, when given an XML node and a child node, determines whether
          the child node should be treated as separate entity that has been embedded.
          Please refer to existing import modules such as for STIX or OpenIOC for
          examples of how to use this parameter.

        - id_and_revision_extractor:
          A function that, when given an XML node and a child node, determines whether
          this node specifies an identifier and possibly a timestamp.
          Please refer to existing import modules such as for STIX or OpenIOC for
          examples of how to use this parameter.

        - extract_empty_embedded:
          A flag (True/False) governing whether elements that are recognized as
          being embedded but contain no childs should be extracted as separate
          object or not. The default is False; the setting "True" may be necessary
          in cases where there are embedded objects that contain all its information
          in attributes rather than using child elements.

        - keep_attrs_in_created_reference:
          A flag (True/False) governing the shape of the reference created for
          an embedded object: when an embedding is recognized, it is extracted
          and a reference using 'idref' inserted instead. If 'keep_attrs_in_created_reference'
          is True, then the top-level attributes contained in the found embedded object
          are also retained in the reference.


        - transformer:
          A function that, when given an element name and a DingoObjDict containing
          the result of importing the contents under the element of the given name,
          may or may not change the element name and transform the DingoObjDict.
          Please refer to existing import MANTIS modules such as for OpenIOC for
          examples of how to use this parameter.


        Note: a good starting point for understanding how to use the python bindings
        of libxml2 is http://mikekneller.com/kb/python/libxml2python/part1.
        """

        generated_id_count = {}



        # Fill defaults
        if not ns_mapping:
            nas_mapping = {}
        if not transformer:
            transformer = lambda x, y: (x, y)

        # We use the _import_pending_stack to hold extracted embedded objects
        # that still need to be processed
        _import_pending_stack = deque()

        # We collect the read embedded objects in the following list
        embedded_objects = deque()

        def xml_import_(element, depth=0, type_info=None, inherited_id_and_rev_info=None):
            """
            Recursive import function
            """

            if not inherited_id_and_rev_info:
                inherited_id_and_rev_info = main_id_and_rev_info.copy()

            fresh_inherited_id_and_rev_info = inherited_id_and_rev_info.copy()


            if element.name == 'comment':
                return None


            #try:
            #    namespace = element.ns()
            #    ns_mapping[namespace.name]=namespace.content
            #except:
            #    pass

            result = DingoObjDict()

            # Add properties to result dictionary for this element

            if element.properties:
                for prop in element.properties:

                    if not prop:
                        break
                    if prop.type == 'attribute':
                        try:
                            result["@%s:%s" % (prop.ns().name, prop.name)] = prop.content
                        except:
                            result["@%s" % prop.name] = prop.content



            # see if there is a namespace

            try:
                ns = element.ns().name
                result["@@ns"] = ns
            except:
                pass

            # prepare list for keeping resulting dictionaries of child elements

            element_dicts = []

            # While looking at the child-elements, we have to keep track
            # of certain data.

            # Firstly: keep track whether we have seen text content that is not whitespace --
            # if that happens, we know that this element contains mixed
            # content and we will back off and just dump the element contents
            # as is as value into the dictionary.

            non_ws_content = False

            # Secondly: If the element contains cdata stuff, we will see
            # that one (well, the only) child has type cdata. So if
            # we find such a child, we set the flag

            cdata_content = False

            # Thirdly: we keep track of how many different child-element-names
            # we have seen. 
            #
            # - If we find that we have exactly one distinct name,
            #   we will generate a dictionary of form
            #             {<Element_Name> : [ <list of child elemen dictionaries> ]}
            # - If we find that we have as many distinct names as we
            #   child elements, we create a dictionary mapping each child element
            #   name to its dictionary representation
            # - If we find that we have less child element names than
            #   we have children, we know that at least one name
            #   occured more than once. Our dictionary representation cannot
            #   deal with that, and we back off and dump the contents as they
            #   are marked as 'xml' content with the '@@type' attribute.

            name_set = {}

            previous_seen_child = None
            double_occurrance = False

            element_child_count = 0
            child = element.children
            while child is not None:

                #if child_name=='comment':
                #    pass
                if child.name == 'text':
                    # If we have non-whitespace content in one of the children,
                    # we set the non_ws_content flag
                    content = child.content.strip()
                    if content != "":
                        non_ws_content = True

                elif child.type == 'cdata':
                    logger.debug("!!!!FOUND CDATA")
                    # If one of the children (actually, it should be the only child)
                    # has type cdata, we know that the parent element contains cdata
                    # and set the cdata_content flag accordingly
                    cdata_content = True
                else:
                    # we have found an element, so we recurse into it.
                    element_child_count += 1
                    if previous_seen_child and (child.name in name_set) and (not child.name == previous_seen_child):
                        double_occurrance = True

                    name_set[child.name] = None

                    if embedded_predicate:
                        embedded_ns = embedded_predicate(element, child, ns_mapping)
                        logger.debug("Embedded ns is %s" % embedded_ns)

                        if embedded_ns:
                            inherited_id_and_rev_info = fresh_inherited_id_and_rev_info.copy()
                            # There is an embedded object. We therefore
                            # replace the contents of the element with an element
                            # containing an idref (and, since we might need them,
                            # all attributes of the embedded element)

                            if type(embedded_ns) == type({}):
                                # If necessary, the embedded_predicate can return more information
                                # than namespace information, namely we can can hand down
                                # id and revision info that has been derived wenn the embedding
                                # was detected. For backward compatibility,
                                # we further allow returning of a string; if, however,
                                # a dictionary is returned, there is id_and_revision_info.
                                id_and_revision_info = embedded_ns.get('id_and_revision_info',
                                                                       id_and_revision_extractor(child))
                                embedded_ns = embedded_ns.get('embedded_ns',None)
                            else:
                                id_and_revision_info = id_and_revision_extractor(child)


                            # See whether stuff needs to be inherited
                            if not 'id' in id_and_revision_info or not id_and_revision_info['id']:
                                if 'id' in inherited_id_and_rev_info:
                                    parent_id = inherited_id_and_rev_info['id']
                                    if parent_id in generated_id_count:
                                        gen_counter = generated_id_count[parent_id]
                                        gen_counter +=1
                                    else:
                                        gen_counter = 0
                                    generated_id_count[parent_id] = gen_counter
                                    (parent_namespace, parent_uid) = parent_id.split(':')
                                    generated_id = "%s:emb%s-in-%s" % (parent_namespace,gen_counter,parent_uid)
                                    logger.info("Found embedded %s without id and generated id %s" % (element.name,generated_id))
                                    id_and_revision_info['id'] = generated_id
                                    id_and_revision_info['id_inherited'] = True
                                else:
                                    logger.error("Attempt to import object (element name %s) without id -- object is ignored" % elt_name)

                                    #cybox_id = gen_cybox_id(iobject_type_name)

                            if not id_and_revision_info.get('timestamp', None):
                                if inherited_id_and_rev_info and 'timestamp' in inherited_id_and_rev_info:
                                    id_and_revision_info['timestamp'] = inherited_id_and_rev_info['timestamp']
                                    id_and_revision_info['ts_inherited'] = True
                            else:
                                inherited_id_and_rev_info['timestamp'] = id_and_revision_info['timestamp']


                            if 'id' in id_and_revision_info:
                                # If the identifier has no namespace info (this may occur, e.g. for
                                # embedded OpenIOC in STIX, we take the namespace inherited from  the
                                # embedding object
                                if (not ':' in id_and_revision_info['id']
                                    and inherited_id_and_rev_info['id']
                                    and ':' in inherited_id_and_rev_info['id']):
                                    id_and_revision_info['id'] = "%s:%s" % (inherited_id_and_rev_info['id'].split(':')[0],
                                                                            id_and_revision_info['id'])
                                    id_and_revision_info['ns_inherited'] = True

                                inherited_id_and_rev_info['id'] = id_and_revision_info['id']



                            if keep_attrs_in_created_reference:
                                reference_dict = extract_attributes(child, prefix_key_char='@',
                                                                    dict_constructor=DingoObjDict)
                            else:
                                reference_dict = DingoObjDict()

                            reference_dict['@idref'] = id_and_revision_info['id']

                            reference_dict['@@timestamp'] = id_and_revision_info['timestamp']

                            try:
                                reference_dict['@@ns'] = child.ns().name
                            except:
                                reference_dict['@@ns'] = None
                            if embedded_ns == True:
                                embedded_ns = None
                            logger.debug("Setting embedded type info to %s" % embedded_ns)
                            reference_dict['@@embedded_type_info'] = embedded_ns

                            element_dicts.append((child.name, reference_dict))
                            if (child.children or child.content) \
                                or extract_empty_embedded \
                                or 'extract_empty_embedded' in id_and_revision_info:

                                id_and_revision_info['inherited'] = fresh_inherited_id_and_rev_info.copy()
                                if 'inherited' in id_and_revision_info['inherited']:
                                    for key in id_and_revision_info['inherited']['inherited']:
                                        if not key in id_and_revision_info['inherited']:
                                            id_and_revision_info['inherited'][key] = id_and_revision_info['inherited']['inherited'][key]
                                    del(id_and_revision_info['inherited']['inherited'])

                                logger.debug(
                                    "Adding XML subtree starting with element %s and type info %s to pending stack." % (
                                    id_and_revision_info, embedded_ns))
                                _import_pending_stack.append((id_and_revision_info, embedded_ns, child))
                            else:
                                # For example, in cybox 1.0, the following occurs::
                                #         <EmailMessageObj:File xsi:type="FileObj:FileObjectType" object_reference="cybox:object-3cf6a958-5c3f-11e2-a06c-0050569761d3"/>
                                # This is only a reference and may not be confused with the definition of the object,
                                # which occurs someplace else -- otherwise, the (almost) empty reference is created as object
                                # and may overwrite the object resulting from the real definition.
                                logger.info(
                                    "Not adding element %s with type info %s to pending stack because element is empty." % (
                                    id_and_revision_info, embedded_ns))
                        else:
                            child_import = xml_import_(child, depth + 1, inherited_id_and_rev_info=inherited_id_and_rev_info)
                            if child_import:
                                element_dicts.append(child_import)
                    else:
                        child_import = xml_import_(child, depth + 1, inherited_id_and_rev_info=inherited_id_and_rev_info)
                        if child_import:
                            element_dicts.append(child_import)

                child = child.next
                # now, we decide what to do with this node

            distinct_child_count = len(name_set.keys())

            if distinct_child_count == 0:
                # No child elements were detected, so we dump the content into
                # the value
                result['_value'] = element.content
                if cdata_content:
                    # If this is a cdata element, we mark it as such
                    result['@@content_type'] = 'cdata'
            elif non_ws_content == True:
                # We have mixed content, so we dump it
                sub_child = element.children
                serialization = ''
                while sub_child:
                    serialization += sub_child.serialize()
                    sub_child = sub_child.next
                result['_value'] = serialization.strip()
                #result['_value']=element.serialize()
                result['@@content_type'] = 'mixed'
            elif double_occurrance: # distinct_child_count >1 and (distinct_child_count) < element_child_count:
                # We have a structure our dictionary representation cannot
                # deal with -- so we dump it

                logger.warning("Cannot deal with XML structure of %s (children %s, count %s): will dump to value" % (
                element.name, name_set.keys(), element_child_count))
                sub_child = element.children
                serialization = ''
                while sub_child:
                    serialization += sub_child.serialize()
                    sub_child = sub_child.next
                result['_value'] = serialization.strip()
                #result['_value']=element.serialize()
                result['@@content_type'] = 'xml'

            else:

                previously_written_name = None
                for (name, element_dict) in element_dicts:

                    if not previously_written_name or name != previously_written_name:
                        result[name] = element_dict
                        previously_written_name = name
                    else: # if name == previously_written_name:
                        if type(result[name]) == type([]):
                            result[name].append(element_dict)
                        else:
                            result[name] = [result[name], element_dict]
            if type_info:
                result['@@embedded_type_info'] = type_info

            element_ns = None
            try:
                element_ns = element.ns().name
            except:
                pass

            return transformer(element.name, result)


        if xml_content:

            if isinstance(xml_content,libxml2.xmlNode):
                root = xml_content
            else:
                doc = libxml2.parseDoc(xml_content)
                root = doc.getRootElement()

        else:
            doc = libxml2.recoverFile(xml_fname)
            root = doc.getRootElement()
            with open(xml_fname, 'r') as content_file:
                xml_content = content_file.read()







        # Extract namespace information (if any)
        try:
            ns_def = root.nsDefs()
            while ns_def:
                ns_mapping[ns_def.name] = ns_def.content
                ns_def = ns_def.next
        except:
            pass

        # Extract ID and timestamp for root element

        main_id_and_rev_info = id_and_revision_extractor(root)

        # Call the internal recursive function. This returns
        # - name of the top-level element
        # - DingoObjDict resulting from import
        # As side effect, it pushes the XML nodes of
        # found embedded objects onto the pending stack

        (main_elt_name, main_elt_dict) = xml_import_(root, 0)

        # We now go through the pending stack.
        # For each found embedded object, xml_import_ pushes
        # the following triple on the stack:
        # - id_and_revision_info: A dictionary, containing
        #   identifier and (possibly) timestamp information
        #   for that object
        # - type_info: Information about the type of the
        #   embedded object (can be None)
        # - the XML node that describes the embedded object

        do_not_process_list = []

        while _import_pending_stack:
            (id_and_revision_info, type_info, elt) = _import_pending_stack.pop()
            if 'defer_processing' in id_and_revision_info:
                do_not_process_list.append((id_and_revision_info,type_info,elt))

            else:
                (elt_name, elt_dict) = xml_import_(elt, 0,
                                                   type_info=type_info,
                                                   inherited_id_and_rev_info=id_and_revision_info.copy())

                embedded_objects.append({'id_and_rev_info': id_and_revision_info,
                                             'elt_name': elt_name,
                                             'dict_repr': elt_dict})

        result= {'id_and_rev_info': main_id_and_rev_info,
                'elt_name': main_elt_name,
                'dict_repr': main_elt_dict,
                'embedded_objects': embedded_objects,
                'unprocessed' : do_not_process_list,
                'file_content': xml_content}


        #pp.pprint(result)

        return result




    
    
