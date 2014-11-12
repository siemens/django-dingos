import autocomplete_light
from taggit.models import Tag

class TagAutocomplete(autocomplete_light.AutocompleteModelBase):
    model = Tag
    search_fields = ['name', 'slug']
    attrs={
        'placeholder': 'Type Tag here',
        'data-autcomplete-minimum-characters' : 2,
        }
    widget_attrs = {'data-widget-maximum-values': 3}

autocomplete_light.register(Tag, TagAutocomplete)