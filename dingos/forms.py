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
    view = forms.CharField(max_length=256,widget=widgets.HiddenInput)
    new_entry = forms.BooleanField(widget=widgets.HiddenInput,required=False)


class CustomQueryForm(forms.Form):
    query = forms.CharField(required=False,widget=widgets.Textarea(attrs={'cols':100,'rows':10,'style': 'height:auto; width:auto;'}))
    paginate_by = forms.ChoiceField(choices=[(str(x), str(x)) for x in [50,100,200,300,400,500,1000,2]],required=False,initial='100')
    page = forms.IntegerField(required=False,initial=1,widget=forms.HiddenInput)


class EditInfoObjectFieldForm(forms.Form):
    value = forms.CharField(required=True, widget=widgets.TextInput(attrs={'size':10,'class':'vTextField'}))

class SimpleMarkingAdditionForm(forms.Form):
    def __init__(self, request, *args, **kwargs):
        marking_choices = kwargs['markings']
        del(kwargs['markings'])
        if 'checked_objects_choices' in kwargs:
            checked_objects = kwargs['checked_objects_choices']
            del(kwargs['checked_objects_choices'])
        else:
            checked_objects = []
        super(SimpleMarkingAdditionForm, self).__init__(request,*args, **kwargs)
        self.fields['marking_to_add'] = forms.ChoiceField(choices=marking_choices)
        self.fields['checked_objects'] = forms.MultipleChoiceField(choices=(map(lambda x: (x,x),checked_objects)),
                                                                   widget=forms.CheckboxSelectMultiple)
        self.fields['checked_objects_choices'] = forms.CharField(initial=",".join(checked_objects),widget=forms.HiddenInput)


    def checkbox_for_pk(self,pk):
        return self.fields['checked_objects']



