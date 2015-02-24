import autocomplete_light
from taggit.models import Tag

class TagAutocompleteDingos(autocomplete_light.AutocompleteModelBase):
    model = Tag
    search_fields = ['name']
    choices = Tag.objects.all()

    attrs={
        'placeholder': 'Type in tag here..',
        'data-autocomplete-minimum-characters' : 2,
        'id' : "id_tag",
        'data-tag-type' : 'dingos'
        }

autocomplete_light.register(TagAutocompleteDingos)