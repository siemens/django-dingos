import autocomplete_light
from taggit.models import Tag

class TagAutocomplete(autocomplete_light.AutocompleteModelBase):
    model = Tag
    search_fields = ['name']
    choices = Tag.objects.all()

    attrs={
        'placeholder': 'Type in tag here..',
        'data-autocomplete-minimum-characters' : 2
        }

autocomplete_light.register(TagAutocomplete)