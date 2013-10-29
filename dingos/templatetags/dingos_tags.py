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
from django.utils.html import strip_tags
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from dingos import DINGOS_TEMPLATE_FAMILY



register = template.Library()


def node_indent(elt_name, node_id, fact_term, attribute, highlight_node=None):
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
        if is_attr:
            result.append("<%(elt_name)s style='background: %(color)s'>%(fact_term_component)s</%(elt_name)s>" % {
                'elt_name': elt_name,
                'fact_term_component': fact_components.get(counter, ''),
                'color': color_dict[2][max(14 - counter,4)]})
        else:
            result.append(
                "<%(elt_name)s style='width:1px; margin: 0px ; background : %(color)s'>%(fact_term_component)s</%(elt_name)s>" % {
                    'elt_name': elt_name,
                    'color': color_dict[node_mod][max(14 - counter,4)],
                    'fact_term_component': fact_components.get(counter, '')})

        counter += 1

    highlight = "style='background: #FF0000;'" if highlight_node == node_id else None

    result.append("<%(elt_name)s colspan='%(colspan)s' %(highlight)s>" % {'elt_name': elt_name, 'colspan': (indents - counter), 'highlight' : highlight})

    return "".join(result)


register.simple_tag(node_indent)


def node_indent_end(elt_name, node_id, fact_term, attribute):
    """
    Closing tag for the node_indent tag. Currently, only the
    parameter elt_name is used: we keep the other around in
    case we later find out that we need to do some more
    closing stuff based on the contents of the other parameters
    also used in the opening tag.
    """
    return "</%s>" % elt_name

register.simple_tag(node_indent_end)


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

@register.simple_tag
def create_title(*args):
    """
    Combines all given arguments to create clean title-tags values.
    All arguments are divided by a " " seperator and HTML tags
    are to be removed.
    """
    seperator = " "
    return strip_tags(seperator.join(args))


@register.inclusion_tag('dingos/%s/includes/_Paginator.html' % DINGOS_TEMPLATE_FAMILY)
def render_paginator(view,paginator,page_obj):
    request_string = view.get_query_string(remove=['page'])
    return {'request_string':request_string,'paginator':paginator,'page_obj':page_obj}

# Below we register template tags that display
# certain aspects of an InformationObject.

@register.inclusion_tag('dingos/%s/includes/_InfoObjectFactsDisplay.html'% DINGOS_TEMPLATE_FAMILY)
def show_InfoObject(iobject, iobject2facts, view=None, highlight=None,show_NodeID=False):
    page = view.request.GET.get('page')


    #iobject2facts_paginator = Paginator(iobject.fact_thru.all(),100)
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


    return {'object': iobject,
            'view' : view,
            'is_paginated' : is_paginated,
            'paginator' : iobject2facts_paginator,
            'page_obj' :iobject2facts,
            'highlight' : highlight,
            'show_NodeID' : show_NodeID,
            'iobject2facts_paginator':iobject2facts_paginator,
            'iobject2facts': iobject2facts}


@register.inclusion_tag('dingos/%s/includes/_InfoObjectRevisionListDisplay.html'% DINGOS_TEMPLATE_FAMILY)
def show_InfoObjectRevisions(iobject):
    return {'object': iobject}


@register.inclusion_tag('dingos/%s/includes/_InfoObjectRevisionListDisplay_vertical.html'% DINGOS_TEMPLATE_FAMILY)
def show_InfoObjectRevisions_vertical(iobject):
    return {'object': iobject}


@register.inclusion_tag('dingos/%s/includes/_InfoObjectEmbeddingDisplay.html'% DINGOS_TEMPLATE_FAMILY)
def show_InfoObjectEmbeddings(iobject):
    return {'object': iobject}


@register.inclusion_tag('dingos/%s/includes/_InfoObjectEmbeddingDisplay_vertical.html'% DINGOS_TEMPLATE_FAMILY)
def show_InfoObjectEmbeddings_vertical(iobject,max_embedded):
    return {'object': iobject, 'max_embedded' : max_embedded}


@register.inclusion_tag('dingos/%s/includes/_InfoObjectIDDataDisplay.html'% DINGOS_TEMPLATE_FAMILY)
def show_InfoObjectIDData(iobject, show_hyperlink=False,show_title=False):
    return {'object': iobject,
            'show_hyperlink': show_hyperlink,
            'show_title': show_title}


@register.inclusion_tag('dingos/%s/includes/_InfoObjectMarkingsListDisplay.html'% DINGOS_TEMPLATE_FAMILY)
def show_InfoObjectMarkings(iobject):
    return {'object': iobject}
