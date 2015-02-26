__author__ = 'fh'


from django import template

from taggit.models import Tag
from dingos.models import Fact, vIO2FValue, Identifier
from dingos.templatetags.dingos_tags import reachable_packages

from dingos import DINGOS_TEMPLATE_FAMILY

register = template.Library()

from django.core.exceptions import ObjectDoesNotExist
from dingos.forms import InvestigationForm

@register.inclusion_tag('dingos/%s/includes/_InfoObjectTagAndExportToActionables.html' % DINGOS_TEMPLATE_FAMILY,takes_context=True)
def show_InvestigationAction(context,cache_session_key):
    try:
        form = context['view'].form
    except:
        form = InvestigationForm(cache_session_key=cache_session_key)
    return {'form': form}

@register.inclusion_tag('dingos/%s/includes/_TaggedObjectsWidget.html' % DINGOS_TEMPLATE_FAMILY,takes_context=True)
def show_TaggedThings(context,tag,mode='precise',display='factdetail', top_level_fold = 'open'):
    view = context['view']
    context = {}
    model_objects_mapping =  {}

    possible_models = {
            Fact : ['fact_term__term','fact_term__attribute','fact_values__value'],
            Identifier : ['latest__id','latest__name','namespace__uri','uid']
        }
    if mode == 'contains':
        tag_id = Tag.objects.filter(name__contains=tag).values_list('id',flat=True)
    else:
        try:
            tag_id = [Tag.objects.get(name=tag).id]
        except ObjectDoesNotExist:
            tag_id = []
    for model,cols in possible_models.items():
        if model == Fact and display == 'factdetails':
            cols = ['term','attribute','value','iobject_id','fact_id']
            matching_items_tmp = list(vIO2FValue.objects.filter(fact__tag_through__tag__id__in = tag_id).values(*cols))

            matching_items = set()

            fact2parent = {}
            parent2toplevel = {}
            iobj2nodeinfo = {}
            parent_iobj_pks = set()


            for x in matching_items_tmp:
                parent_list = fact2parent.setdefault(x['fact_id'],[])
                parent_list.append(x['iobject_id'])
                parent_iobj_pks.add(x['iobject_id'])
                row = (x['term'],x['attribute'],x['value'],x['fact_id'])
                matching_items.add(row)

            #context['object_list'] = list(parent_iobj_pks)
            for parent_pk in parent_iobj_pks:
                found_top_level_objects = reachable_packages({'view':view,
                                                              'object_list' : list(parent_iobj_pks)},parent_pk)['node_list']
                top_list = parent2toplevel.setdefault(parent_pk,[])
                for (pk,node_info) in found_top_level_objects:
                    top_list.append(pk)
                    if not pk in iobj2nodeinfo.keys():
                        iobj2nodeinfo[pk] = (node_info['identifier_ns'],node_info['identifier_uid'],node_info['name'])

            #retrieve missing iobj infos
            no_info = parent_iobj_pks - set(iobj2nodeinfo.keys())
            infos = vIO2FValue.objects.filter(iobject_id__in=no_info).distinct('iobject_id').values('iobject_id','iobject_identifier_uri','iobject_identifier_uid','iobject_name')
            for x in infos:
                iobj2nodeinfo[x['iobject_id']] = (x['iobject_identifier_uri'],x['iobject_identifier_uid'],x['iobject_name'])

            context['fact2parent'] = fact2parent
            context['parent2toplevel'] = parent2toplevel
            context['iobj2nodeinfo'] = iobj2nodeinfo

        else:
            matching_items = list(model.objects.filter(tag_through__tag__id__in = tag_id).distinct('id').values_list(*cols))

        model_objects_mapping[model.__name__] = matching_items

    context['display'] = display
    context['top_level_fold'] = top_level_fold
    context['view'] = view
    context['tag'] = tag
    context['model_objects_mapping'] = model_objects_mapping

    return context
