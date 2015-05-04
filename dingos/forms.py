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

import re

from django import forms

from django.template import Context, Template

from django.utils.safestring import mark_safe

from django.forms import widgets

from django.core.validators import RegexValidator

from dingos import DINGOS_TAGGING_REGEX, DINGOS_MANTIS_MUTUAL_EXCLUSIVE_TAGS_FUNCTION

from dingos.queryparser.placeholder_parser import PlaceholderException

from taggit.models import Tag
import autocomplete_light


class EditSavedSearchesForm(forms.Form):
    """
    Form for editing a saved search. Used by the respective view.
    """

    title = forms.CharField(required=False, # We allow empty titles -- otherwise
                                            # we cannot have the functionality
                                            # that a new saved search is removed
                                            # if no title is given.
                            max_length=100,
                            widget=widgets.TextInput(attrs={'size':'20','class':'vTextField'}))
    identifier = forms.CharField(required=False,
                                 max_length=20)

    parameter = forms.CharField(max_length=1024,widget=widgets.TextInput(attrs={'class':'vTextField'}))
    custom_query = forms.CharField(required=False,max_length=4096,widget=widgets.Textarea(attrs={'class':'vTextField'}))
    view = forms.CharField(max_length=256,widget=widgets.HiddenInput)
    new_entry = forms.BooleanField(widget=widgets.HiddenInput,required=False)


class CustomQueryForm(forms.Form):
    query = forms.CharField(required=False,widget=widgets.Textarea(attrs={'cols':100,'rows':10,'style': 'height:auto; width:auto;'}))
    _choices = [(str(x), str(x)) for x in [50,100,200,300,400,500,1000,2]]
    _choices.append(('1000000','ALL (DANGER!)'))
    paginate_by = forms.ChoiceField(choices=_choices,required=False,initial='100')
    page = forms.IntegerField(required=False,initial=1,widget=forms.HiddenInput)


class PlaceholderForm(forms.Form):
    fields = None

    def __init__(self, *args, **kwargs):
        placeholders = kwargs.pop("placeholders")
        super(PlaceholderForm, self).__init__(*args, **kwargs)

        for i, one in enumerate(placeholders):
            placeholder = one["parsed"]


            if "default" in placeholder.keys():
                if placeholder.get('widget','TextInput') == 'TextInput':
                    widget = widgets.TextInput(attrs={'size': '100',
                                                      'class': 'vTextField',
                                                      'value': placeholder['default']})
                    self.fields[placeholder['field_name']] = forms.CharField(label=placeholder['human_readable'],
                                                                             required=False,
                                                                             max_length=100,
                                                                             widget=widget)
                elif placeholder['widget'] == 'DateInput':
                    widget = widgets.DateInput(attrs={'size': '10',
                                                      'value': placeholder['default']})
                    self.fields[placeholder['field_name']] = forms.CharField(label=placeholder['human_readable'],
                                                                             required=False,
                                                                             max_length=10,
                                                                             widget=widget)
                else:
                    raise PlaceholderException("Widget \"%s\" is not supported." % placeholder['widget'])
            else:
                raise PlaceholderException("A default is mandatory for a placeholder.")



class EditInfoObjectFieldForm(forms.Form):
    value = forms.CharField(required=True, widget=widgets.TextInput(attrs={'size':10,'class':'vTextField'}))


class BasicListActionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices',[])
        super(BasicListActionForm, self).__init__(*args, **kwargs)

        self.fields['checked_objects'] = forms.MultipleChoiceField(choices=(map(lambda x: (x,x),choices)),
                                                                   widget=forms.CheckboxSelectMultiple)
        self.fields['checked_objects_choices'] = forms.CharField(widget=forms.HiddenInput)


class SimpleMarkingAdditionForm(BasicListActionForm):
    def __init__(self, *args, **kwargs):
        marking_choices = kwargs.pop('markings')
        allow_multiple_markings = kwargs.pop('allow_multiple_markings',None)

        super(SimpleMarkingAdditionForm, self).__init__(*args, **kwargs)
        if allow_multiple_markings:
            self.fields['marking_to_add'] = forms.MultipleChoiceField(choices=marking_choices)
        else:
            self.fields['marking_to_add'] = forms.ChoiceField(choices=marking_choices)

class TaggingAdditionForm(BasicListActionForm):
    def __init__(self, *args, **kwargs):
        tagging_choices = kwargs.pop('tags',[])
        allow_multiple_tags = kwargs.pop('allow_multiple_tags',None)
        super(TaggingAdditionForm, self).__init__(*args, **kwargs)
        if allow_multiple_tags:
            self.fields['tag_to_add'] = forms.MultipleChoiceField(choices=tagging_choices)
        else:
            self.fields['tag_to_add'] = forms.ChoiceField(choices=tagging_choices)
        self.fields['comment'] = forms.CharField(widget=forms.Textarea,required=False)

class OAuthInfoForm(forms.Form):
    """
    Form for editing the OAuth information. Used by the respective view.
    """
    client_name = forms.CharField(required=True, max_length=100, widget=widgets.TextInput(attrs={'size': '100', 'class': 'vTextField'}))
    client_id = forms.CharField(required=True, max_length=100, widget=widgets.TextInput(attrs={'size': '100', 'class': 'vTextField'}))
    client_secret = forms.CharField(required=True, max_length=200, widget=widgets.TextInput(attrs={'size': '200', 'class': 'vTextField'}))


class OAuthNewClientForm(forms.Form):
    """
    Form to generate a new OAuth client. Used by the respective view.
    """
    new_client = forms.CharField(required=True, max_length=100, widget=widgets.TextInput(attrs={'size': '100', 'class': 'vTextField'}))



tag_validators = []

for regex in DINGOS_TAGGING_REGEX:
    tag_validators.append(RegexValidator(regex,"Not a valid tag"))



def check_tag_validity(tag,
                       run_regexp_checks=False,
                       raise_exception_on_problem=True):
    """
    Checks the validity of a tag by performing the following actions:

    - check against regular expressions configured in list 'DINGOS_TAGGING_REGEX'
    - checks whether the provided tag has a mutually exclusive tag (defined
      via function DINGOS_MANTIS_MUTUAL_EXCLUSIVE_TAGS_FUNCTION). If so,
      the function checks, whether the mutually exclusive tag does already
      exist. If that is the case, then validation fails.

    With the argument ``raise_exception_on_problem``, we can configure,
    whether a validation error is raised if problems occur.
    if ``raise_exception_on_problem`` is set to ``False``, the behavior
    is as follows:

    - if the regex check fails, ``None`` is returned
    - if a mutually exclusive tag exists, that tag is returned rather
      that the tag provided to the user. Hence, the existing mutually
      exclusive tag is used.

    ATTENTION: This function is used in the import task of mantis_authoring!!!

    """
    if run_regexp_checks:
        valid = False
        for regex in DINGOS_TAGGING_REGEX:
            if regex.match(tag):
                valid = True
                break

        if not valid:
            if raise_exception_on_problem:
                raise forms.ValidationError("'%s' is not a valid tag" % tag)
            else:
                # Tag is invalid and cannot be used
                return None

    mutually_exclusive_sibling = DINGOS_MANTIS_MUTUAL_EXCLUSIVE_TAGS_FUNCTION(tag)
    if mutually_exclusive_sibling:
        existing_tags = Tag.objects.filter(name=mutually_exclusive_sibling)
        if existing_tags:
            if raise_exception_on_problem:
                raise forms.ValidationError("Cannot apply tag %s, because mutually exclusive tag %s already exists" % (tag,mutually_exclusive_sibling))
            else:
                # Use mutually exclusive sibling instead
                return mutually_exclusive_sibling
        from mantis_actionables.models import Context
        existing_tags = Context.objects.filter(name=mutually_exclusive_sibling)
        if existing_tags:
            if raise_exception_on_problem:
                raise forms.ValidationError("Cannot apply tag %s, because mutually exclusive tag %s already exists" % (tag,mutually_exclusive_sibling))
            else:
                # Use mutually exclusive sibling instead
                return mutually_exclusive_sibling

    return tag

class TagForm(autocomplete_light.ModelForm):
    tag = autocomplete_light.ChoiceField(widget =
                                         autocomplete_light.TextWidget('TagAutocompleteDingos'
                                                                       #,attrs={'placeholder': 'Aha'}
                                                                                ),
                                         validators= tag_validators
                                         )
    class Meta:
        model = Tag
        exclude = ['slug', 'name']

    def clean(self):
        cleaned_data = super(InvestigationForm, self).clean()
        investigation_tag = cleaned_data.get("investigation_tag")
        check_tag_validity(investigation_tag,
                           # Regexp validators have already been run by form
                           run_regexp_checks=False,
                           raise_exception_on_problem=True)
        return cleaned_data




class MCFieldAccessForm(forms.Form):
    mc_field_by_value = {}

    def init_mc_field_dict(self,field_name):
        result = {}
        self.mc_field_by_value[field_name] = result
        context = Context({'form':self})
        all_checked_item_fields = Template(""" {%% for option in form.%s %%}
                {{ option.tag }}
              {%% endfor %%}""" % field_name).render(context)
        for match in re.finditer("""(?P<field_start><input.*?value=")(?P<pk>[0-9]+)(?P<field_end>.*?/>)""",all_checked_item_fields):
            match_dict = match.groupdict()
            try:
                pk = int(match_dict['pk'])
            except:
                pk = match_dict['pk']
            result[pk] = mark_safe("%s%s%s" % (match_dict['field_start'],
            match_dict['pk'],
            match_dict['field_end']))




class ResultActionForm(MCFieldAccessForm):
    """


    """

    def __init__(self,*args,**kwargs):
        cache_session_key = kwargs.pop('cache_session_key',"")
        result_len = kwargs.pop('result_len',0)
        result_pks = kwargs.pop('result_pks',[])
        hide_choices = kwargs.pop('hide_choices',False)

        if hide_choices:
            checked_item_widget = forms.widgets.MultipleHiddenInput()
        else:
            checked_item_widget = forms.CheckboxSelectMultiple(attrs={'class':'action-select'})

        super(ResultActionForm, self).__init__(*args, **kwargs)

        self.fields['cache_session_key'] = forms.CharField(initial=cache_session_key,
                                                           required=False,
                                                           widget=forms.widgets.HiddenInput())
        self.fields['result_len'] = forms.IntegerField(initial=result_len,
                                                       required=False,
                                                       widget=forms.widgets.HiddenInput())

        if result_len:
            self.fields['checked_items'] = forms.MultipleChoiceField(
                                                                     map(lambda x: (x,x), range(0,result_len)),
                                                                     required=False,
                                                                     initial=range(0,result_len),
                                                                     widget=checked_item_widget)
        elif result_pks:
            self.fields['checked_items'] = forms.MultipleChoiceField(
                                                                     map(lambda x: (x,x), result_pks),
                                                                     required=False,
                                                                     initial=range(0,result_len),
                                                                     widget=checked_item_widget)

        self.init_mc_field_dict('checked_items')





class InvestigationForm(ResultActionForm):

    investigation_tag = forms.CharField(widget =
                                         autocomplete_light.TextWidget('TagInvestigationAutocompleteDingos'                                                                                ),
                                         validators= tag_validators
                                         )


    def clean(self):
        cleaned_data = super(InvestigationForm, self).clean()
        investigation_tag = cleaned_data.get("investigation_tag","")

        check_tag_validity(investigation_tag,
                           run_regexp_checks=False,
                           raise_exception_on_problem=True)

        return cleaned_data
