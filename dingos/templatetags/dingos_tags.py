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

from django import template
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse
from django.utils import html
from django.utils.html import conditional_escape, strip_tags
from django.utils.safestring import mark_safe

from dingos import DINGOS_TEMPLATE_FAMILY
from dingos.core import http_helpers
from dingos.core.utilities import get_from_django_obj
from dingos.models import BlobStorage

from dingos.graph_traversal import follow_references
from dingos.graph_utils import dfs_preorder_nodes

from dingos.models import InfoObject, InfoObject2Fact




register = template.Library()


def node_indent(context,
                elt_name, node_id, fact_term, attribute, highlight_node=None):
    """
    This tag uses a table structure to display indentation
    of fact terms based on the information contained in the
    node identifier.

    This tag and the closing 'node_indent_end' tag must
    enclose the value to be displayed after the display
    of the fact term.

    """
    # Some colors to chose from:
    color_dict = {0: {0: '#004C80', # blueish
                      1: '#005C99',
                      2: '#006BB2',
                      3: '#007ACC',
                      4: '#008AE6',
                      5: '#0099FF',
                      6: '#19A3FF',
                      7: '#33ADFF',
                      8: '#4DB8FF',
                      9: '#66C2FF',
                      10: '#80CCFF',
                      11: '#99D6FF',
                      12: '#B2E0FF',
                      13: '#CCEBFF',
                      14: '#E6F5FF'},
                  2: {0: '#008000', # greenish
                      1: '#009900',
                      2: '#00B200',
                      3: '#00CC00',
                      4: '#00E600',
                      5: '#00FF00',
                      6: '#19FF19',
                      7: '#33FF33',
                      8: '#4DFF4D',
                      9: '#66FF66',
                      10: '#80FF80',
                      11: '#99FF99',
                      12: '#B2FFB2',
                      13: '#CCFFCC',
                      14: '#E6FFE6'},
                  3: {0: '#804C80', # pinkish
                      1: '#995C99',
                      2: '#B26BB2',
                      3: '#CC7ACC',
                      4: '#E68AE6',
                      5: '#FF99FF',
                      6: '#FFA3FF',
                      7: '#FFADFF',
                      8: '#FFB8FF',
                      9: '#FFC2FF',
                      10: '#FFCCFF',
                      11: '#FFD6FF',
                      12: '#FFE0FF',
                      13: '#FFEBFF',
                      14: '#FFF5FF', },
                  1: {0: "#5C3D99", # violetish
                      1: "#6B47B2",
                      2: "#7A52CC",
                      3: "#8A5CE6",
                      4: "#9966FF",
                      5: "#A375FF",
                      6: "#AD85FF",
                      7: "#B894FF",
                      8: "#C2A3FF",
                      9: "#CCB2FF",
                      10: "#D6C2FF",
                      11: "#E0D1FF",
                      12: "#EBE0FF",
                      13: "#F5F0FF",
                      14: "#FFFFFF"}

    }

    indents = 100
    node_ids = node_id.split(':')
    fact_components = fact_term.split('/')

    if len(fact_components) == 1 and fact_components[0] == '':
        fact_components = []
    if attribute:
        fact_components.append("@%s" % attribute)

    fact_components = dict([(x, fact_components[x]) for x in range(0, len(fact_components))])


    #node_ids.reverse()

    result = []
    counter = 0
    sticky_color =None
    previous_color= None


    for node in node_ids:

        is_attr = False
        if len(node) >= 1:
            if node[0] == 'A':
                is_attr = True

            node = node[1:]

        if len(node) > 0:
            node_nr = int(node)
        else:
            node_nr = 0
        if is_attr:
            node_mod = 2
        else:
            node_mod = node_nr % 2

        if sticky_color:
            color = sticky_color
        else:
            color = color_dict[node_mod][max(14 - counter,4)]


        if counter in context['row_map'][tuple(node_ids)]:

            if is_attr:
                row_span = 1
                if previous_color:
                    attr_color = """style='background: %s'""" % previous_color
                else:
                    attr_color = ''
                result.append("<%(elt_name)s %(color)s rowspan='%(row_span)s'>  %(fact_term_component)s</%(elt_name)s>" % {
                    'elt_name': elt_name,
                    'fact_term_component': insert_wbr(fact_components.get(counter, '')),
                    'color': attr_color, #color,
                    'row_span': row_span})
            else:
                row_span = context['row_map'][tuple(node_ids)][counter]
                if row_span == 1:
                    sticky_color = color
                result.append(
                    "<%(elt_name)s style='width:1px; margin: 0px ; background : %(color)s' rowspan='%(row_span)s'>%(fact_term_component)s</%(elt_name)s>" % {
                        'elt_name': elt_name,
                        'color': color,
                        'fact_term_component': insert_wbr(fact_components.get(counter, '')),
                        'row_span': row_span
                    })

        counter += 1
        previous_color = color

    highlight = "style='background: #FF0000;'" if highlight_node == node_id else None


    result.append("<%(elt_name)s colspan='%(colspan)s' %(highlight)s>" % {'elt_name': elt_name, 'colspan': (indents - counter), 'highlight' : highlight})

    return "".join(result)


register.simple_tag(node_indent,takes_context=True)

def node_indent_end(context, elt_name, node_id, fact_term, attribute):
    """
    Closing tag for the node_indent tag. Currently, only the
    parameter elt_name is used: we keep the other around in
    case we later find out that we need to do some more
    closing stuff based on the contents of the other parameters
    also used in the opening tag.
    """
    return "</%s>" % elt_name

register.simple_tag(node_indent_end,takes_context=True)



@register.simple_tag
def render_formset_form(formset, formindex, key, field):    
    """ 
    Outpts a (plain) rendered field of an formset.
    The formindex[key] determines which form to take 
    from the set. Only a given field will be rendered.
    """
    return formset[formindex[key][0]][field]





@register.filter(needs_autoescape=True)
def insert_wbr(value,autoescape=None):
    """
    """
    if autoescape:
        esc = conditional_escape
    else:
        esc = lambda x:x
    return mark_safe(esc("%s" % value).replace('/','/<wbr>').replace('0','0<wbr>').replace('_','_<wbr>'))

@register.filter
def sliceupto(value, upto):
    """
    An additional slice feature working with int variables
    which can be set within the context of a view.
    Usage in template: {% for obj in list|sliceupto:z %}
    """
    try:
        return value[0:upto]
    except (ValueError, TypeError):
        return value



@register.inclusion_tag('dingos/%s/includes/_TableOrdering.html' % DINGOS_TEMPLATE_FAMILY,takes_context=True)
def render_table_ordering(context, index, title):
    """
    Renders a TABLE LAYOUT ordering using given index and a human-readable title for it.
    Note that a new context is created for the template (containing only very few elements needed
    for displaying).

    Usage in template: {% render_table_ordering "model_field__submodel_field" "Human-readable Title" %}
    """

    # title + plain url (=without o paramater)
    new_context = { 'title' : title, 'plain_url' : context['view'].get_query_string(remove=['o']) }

    # ordered url
    new_context['ordered_url'] = new_context['plain_url'] + '&o=' + index

    # toggled ordering url (only if needed)
    if 'o' in context['request'].GET and ( context['request'].GET['o'] == index or context['request'].GET['o'] == '-%s' % index):
        new_context['toggled_url'] = new_context['plain_url'] + '&o=' + (index if context['request'].GET['o'].startswith('-') else '-' + index) 
        new_context['order_direction'] = 'ascending' if context['request'].GET['o'].startswith('-') else 'descending'

    return new_context


@register.simple_tag
def lookup_blob(hash_value):
    """
    Combines all given arguments to create clean title-tags values.
    All arguments are divided by a " " seperator and HTML tags
    are to be removed.
    """
    try:
        blob = BlobStorage.objects.get(sha256=hash_value)
    except:
        return "Blob not found"
    return html.escape(blob.content)


@register.simple_tag
def create_title(*args):
    """
    Combines all given arguments to create clean title-tags values.
    All arguments are divided by a " " seperator and HTML tags
    are to be removed.
    """
    seperator = " "
    return strip_tags(seperator.join(args))


#@register.simple_tag
#def url_from_query(*args,url=None):
#    
#    if not remove:
#        remove=[]
#    request_string = context['view'].get_query_string(remove=remove)
#    return "%s%s" % (reverse(url),request_string) 

@register.inclusion_tag('dingos/%s/includes/_Paginator.html' % DINGOS_TEMPLATE_FAMILY,takes_context=True)
def render_paginator(context,is_counting=True):
    if 'counting_paginator' in dir(context['view']):
        is_counting = context['view'].counting_paginator
    else:
        is_counting = True

    request_string = context['view'].get_query_string(remove=['page'])
    return {'request_string':request_string,'paginator':context['paginator'],'page_obj':context['page_obj'],
            'paginate_by': context['view'].paginate_by, 'object_list_len': context.get('object_list_len',0),
            'counting_paginator': is_counting}

# Below we register template tags that display
# certain aspects of an InformationObject.

@register.inclusion_tag('dingos/%s/includes/_InfoObjectFactsDisplay.html'% DINGOS_TEMPLATE_FAMILY,takes_context=True)
def show_InfoObject(context,
                    formset=None,
                    formindex=None,
                    iobject2facts=None,
                    title='Facts',
                    fold_status='open',
                    header_level=2,
                    io2f_pred = None,
                    close_div=True,
                    inner_collapsible = False,
                    inner_fold_status = 'open'):

    page = context['view'].request.GET.get('page')

    iobject = context['view'].object
    if not iobject2facts:
        iobject2facts = context['view'].iobject2facts
    highlight = context['highlight']
    show_NodeID = context['show_NodeID']

    def rowspan_map(iobject2facts):
        """
        When displaying the fact-term--value pairs, we want to
        use row-spans. Instead of

        +-------------+-----------------+
        | blah | foo  |                 |
        +------+------+-----------------+
        | blah | bar  |                 |
        +------+------+-----------------+


        we want to display

        +-------------+-----------------+
        |      | foo  |                 |
        | blah |------+-----------------+
        |      | bar  |                 |
        +------+------+-----------------+

        Since we iterate through the fact-term--value pairs with a loop,
        and the rowspan has to be specified in the very first row,
        we have to precalculate the row-span per indentation level.
        This is what this function does: for each node identifier,
        it calculates a dictionary mapping indentation levels to
        rowspans like so::

           rowspan_map[('N000','N000','N000')] = {0: 9, 1: 9, 2: 1}

        This means that on level 0, there should be a row span of 9,
        at level 1, also of 9 and at level 2 of 1.

        """

        row_map = {}
        row_span_start = {}
        previous_node = []
        for io2f in iobject2facts:
            node_id = io2f.node_id.name.split(':')
            node_id_tuple = tuple(node_id)
            row_map[node_id_tuple] = {}
            comparison = zip(previous_node,node_id)
            counter = 0
            wipe = False

            for (previous,this) in comparison:
                if previous == this and not wipe:
                    row_map[row_span_start[counter]][counter] += 1
                else:
                    row_span_start[counter] = node_id_tuple
                    row_map[node_id_tuple][counter] = 1
                    wipe = True
                counter += 1
            for i in range(counter,len(node_id)):
                row_span_start[i] = node_id_tuple
                row_map[node_id_tuple][i] = 1
            previous_node = node_id
        return row_map

    iobject2facts_paginator = Paginator(iobject2facts,200)
    if iobject2facts_paginator.num_pages == 1:
        is_paginated = False
    else:
        is_paginated = True
    try:
        iobject2facts = iobject2facts_paginator.page(page)
        is_paginated=True
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        iobject2facts = iobject2facts_paginator.page(1)

    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        iobject2facts = iobject2facts_paginator.page(iobject2facts_paginator.num_pages)

    if io2f_pred:
        iobject2facts = [io2f for io2f in iobject2facts if io2f_pred[0](io2f)]

    return {'object': iobject,
            'view' : context['view'],
            'is_paginated' : is_paginated,
            'paginator' : iobject2facts_paginator,
            'page_obj' :iobject2facts,
            'highlight' : highlight,
            'show_NodeID' : show_NodeID,
            'iobject2facts_paginator':iobject2facts_paginator,
            'iobject2facts': iobject2facts,
            'row_map' : rowspan_map(iobject2facts),
            'formindex' : formindex,
            'formset' : formset,
            'fold_status' : fold_status,
            'title': title,
            'header_level' : map(str, range(header_level,10)),
            'close_div' : close_div,
            'inner_collapsible': inner_collapsible,
            'inner_fold_status': inner_fold_status}


@register.inclusion_tag('dingos/%s/includes/_InfoObjectRevisionListDisplay.html'% DINGOS_TEMPLATE_FAMILY,takes_context=True)
def show_InfoObjectRevisions(iobject):
    return {'object': iobject}


@register.inclusion_tag('dingos/%s/includes/_InfoObjectRevisionListDisplay_vertical.html'% DINGOS_TEMPLATE_FAMILY)
def show_InfoObjectRevisions_vertical(iobject):
    return {'object': iobject}


@register.inclusion_tag('dingos/%s/includes/_InfoObjectEmbeddingDisplay.html'% DINGOS_TEMPLATE_FAMILY,takes_context=True)
def show_InfoObjectEmbeddings(context,iobject):
    return {'object': iobject,
            'customization' : context.get('customization')}



@register.inclusion_tag('dingos/%s/includes/_InfoObjectEmbeddingDisplay_vertical.html'% DINGOS_TEMPLATE_FAMILY, takes_context=True)
def show_InfoObjectEmbeddings_vertical(context,iobject):
    return {'object': iobject, 'customization' : context.get('customization')}



@register.inclusion_tag('dingos/%s/includes/_InfoObjectIDDataDisplay.html'% DINGOS_TEMPLATE_FAMILY)
def show_InfoObjectIDData(iobject, show_hyperlink=False,show_title=False):
    return {'object': iobject,
            'show_hyperlink': show_hyperlink,
            'show_title': show_title}


@register.inclusion_tag('dingos/%s/includes/_InfoObjectMarkingsListDisplay.html'% DINGOS_TEMPLATE_FAMILY)
def show_InfoObjectMarkings(iobject):
    return {'object': iobject}

@register.inclusion_tag('dingos/%s/includes/_InfoObjectAuthoredDataDisplay_vertical.html'% DINGOS_TEMPLATE_FAMILY)
def show_AuthoringSource(iobject):
    if 'yielded_by' in dir(iobject):
        authored_data_info = iobject.yielded_by.all().order_by('-timestamp')
    else:
        authored_data_info = None
    return {'authored_data_info': authored_data_info}



@register.inclusion_tag('dingos/%s/includes/_InfoObjectGraphDisplay.html'% DINGOS_TEMPLATE_FAMILY)
def show_InfoObjectGraph(iobject):
    return {'object': iobject}


@register.simple_tag
def show_InfoObjectField(oneObject, field):
    """
    Outputs one field of an InfoObject.
    """
    if field == None:
        return "ERROR"
    result = oneObject
    fields = field.split('.')
    result = get_from_django_obj(result,fields)
    if isinstance(result,list):
        return ', '.join(result)
    else:
        return result


@register.assignment_tag(takes_context=True)
def obj_by_pk(context, *args,**kwargs):
    return getattr(context['view'],'obj_by_pk')(*args,**kwargs)

@register.filter
def nice_name(user):
    """
    Example::
    
        Hi, {{ user|nice_name }}
    """
    return user.get_full_name() or user.username


@register.simple_tag
def highlight_if_equal(v1,v2):
    if str(v1)==str(v2):
        return "style='background: #FF0000;'"
    else:
        return ""

@register.simple_tag(takes_context=True)
def reachable_packages(context, current_node):
    view = context["view"]

    # The graph is generated just once per search request
    if not view.graph:

        object_list = context['object_list']


        if object_list:

            if isinstance(object_list[0],InfoObject):
                pks = [one.pk for one in object_list]
            elif isinstance(object_list[0],InfoObject2Fact):
                pks = [one.iobject.pk for one in object_list]
            else:
                pks = []
        view.graph = follow_references(pks, direction= 'up')

    node_ids = list(dfs_preorder_nodes(view.graph, source=current_node))

    if view.graph.node:
        result = []
        for id in node_ids:
            node = view.graph.node[id]
            # TODO: Below is STIX-specific and should be factored out
            # by making the iobject type configurable
            if "STIX_Package" in node['iobject_type']:
                result.append("<a href='%s'>%s</a>" % (node['url'], node['name']))

        return ",<br/> ".join(result)
    else:
        return ''
