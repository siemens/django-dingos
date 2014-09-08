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

from django import forms

from django.forms import widgets

from dingos.queryparser.placeholder_parser import PlaceholderException

class EditSavedSearchesForm(forms.Form):
    """
    Form for editing a saved search. Used by the respective view.
    """
    title = forms.CharField(required=False, # We allow empty titles -- otherwise
                                            # we cannot have the functionality
                                            # that a new saved search is removed
                                            # if no title is given.
                            max_length=100,
                            widget=widgets.TextInput(attrs={'size':'100','class':'vTextField'}))
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
    def __init__(self, request, *args, **kwargs):
        if 'checked_objects_choices' in kwargs:
            checked_objects = kwargs['checked_objects_choices']
            del(kwargs['checked_objects_choices'])
        else:
            checked_objects = []
        super(BasicListActionForm, self).__init__(request,*args, **kwargs)

        self.fields['checked_objects'] = forms.MultipleChoiceField(choices=(map(lambda x: (x,x),checked_objects)),
                                                                   widget=forms.CheckboxSelectMultiple)
        self.fields['checked_objects_choices'] = forms.CharField(widget=forms.HiddenInput)


class SimpleMarkingAdditionForm(BasicListActionForm):
    def __init__(self, request, *args, **kwargs):

        marking_choices = kwargs.pop('markings')
        allow_multiple_markings = kwargs.pop('allow_multiple_markings',None)

        super(SimpleMarkingAdditionForm, self).__init__(request,*args, **kwargs)
        if allow_multiple_markings:
            self.fields['marking_to_add'] = forms.MultipleChoiceField(choices=marking_choices)
        else:
            self.fields['marking_to_add'] = forms.ChoiceField(choices=marking_choices)

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
