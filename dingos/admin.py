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


from django.contrib import admin

from models import DataTypeNameSpace,\
    FactTerm,\
    InfoObjectFamily,\
    Revision,\
    FactTerm2Type,\
    FactDataType,\
    FactValue,\
    Fact,\
    InfoObjectType,\
    InfoObject2Fact,\
    Relation,\
    InfoObject,\
    Identifier,\
    NodeID,\
    InfoObjectNaming,\
    BlobStorage



#
# Inline Interfaces
# -----------------
#
# Django offers the possibility to enrich an admin
# interfaces with admin areas for related objects
# that are 'inlined' into the main interface.
# To achieve this, Inline-classes have to
# be defined.
#
# We use the following naming convention:
#
# XXXXXXX[_zzzzzz_][_]YYYYYYYInline
#
# means that object XXXXXX contains an inline for object YYYYYYYY.
# 'zzzzzz' may be used if the same YYYYYY object is inlined in several
# ways according to multiple relations between XXXXXX and YYYYYY -- see
# examples below).  Underbars may be used to separate names where
# camel-casing gets to confusing.
#
# In inline interface, use the properties 'verbose_name' and 'verbose_name_plural'
# to provide information about the way in which inlines are related to the
# main object.
#
#


class InfoObjectType_InfoObjectNaming_Inline(admin.TabularInline):
    model = InfoObjectNaming
    extra = 0
    fields=('format_string','position')
    sortable_field_name = 'position'


class NameSpace_FactDataType_Inline(admin.TabularInline):
    model = FactDataType
    extra = 0
    fields=('name','description')
    readonly_fields = ('description',)

class FactTerm_FactTerm2Type_Inline(admin.TabularInline):
    model = FactTerm2Type
    extra = 0
    fields = ('iobject_type','fact_data_types',)
    raw_id_fields = ('iobject_type','fact_data_types')

    autocomplete_lookup_fields = {
        'fk': ['iobject_type',],
        'm2m': ['fact_data_types',],
    }



class InfoObject_InfoObject2Fact_Inline(admin.TabularInline):
    model = InfoObject2Fact
    extra = 0
    fields = ('node_id','fact')
    readonly_fields = ('node_id','fact')



#
# Admin Interfaces
# ----------------
#
# Below we specify admin interfaces in which
# we tweak the behavior of the standard admin
# interface:
#
# - list_display: which fields to display in the list of objects
# - list_filter: which fields can be used for filtering the list of objects
# - inlines: which admin interfaces should be inlined?
#
# We also hook into the save-on-change/create mechanism
# to do additional changes where necessary.
#
#

class FactValueAdmin(admin.ModelAdmin):
    list_display = ('value','fact_data_type','storage_location')
    raw_id_fields = ('fact_data_type',)
    autocomplete_lookup_fields = {
        'fk': ['fact_data_type'],
        'm2m': [],
    }


class FactDataTypeAdmin(admin.ModelAdmin):
    list_display = ('name','kind','name_space')
    raw_id_fields = ('name_space',)
    autocomplete_lookup_fields = {
        'fk': ['name_space'],
        'm2m': [],
    }


class NameSpaceAdmin(admin.ModelAdmin):
    list_display = ('uri','name',)
    #filter_horizontal = ('factdatatype_set',)
    inlines = (NameSpace_FactDataType_Inline,)

class InfoObjectTypeAdmin(admin.ModelAdmin):
    list_display = ('name','iobject_family','namespace')
    inlines = (InfoObjectType_InfoObjectNaming_Inline,)


class E2F2AttributeAdmin(admin.ModelAdmin):
    pass

class InfoObject2FactAdmin(admin.ModelAdmin):
    list_display = ('iobject','node_id')


class InfoObjectAdmin(admin.ModelAdmin):
    list_display = ('view_link','iobject_family','iobject_family_revision','iobject_type','iobject_type_revision','name','identifier','timestamp',)
    inlines = (InfoObject_InfoObject2Fact_Inline,)
    raw_id_fields = ('iobject_type',)
    autocomplete_lookup_fields = {
        'fk': ['iobject_type',],
        'm2m': [],
    }


class IdentifierAdmin(admin.ModelAdmin):
    list_display = ('uid','namespace','latest')


class AttributeAdmin(admin.ModelAdmin):
    list_display = ('key','value')

class FactTerm2TypeAdmin(admin.ModelAdmin):
    list_display = ('fact_term','iobject_type')
    raw_id_fields = ('iobject_type','fact_data_types')

    autocomplete_lookup_fields = {
        'fk': ['iobject_type',],
        'm2m': ['fact_data_types',],
    }
 



class FactTermAdmin(admin.ModelAdmin):
    list_display = ('term', )
    inlines = (FactTerm_FactTerm2Type_Inline,)



class InfoObjectFamilyAdmin(admin.ModelAdmin):
    list_display = ('name','title','description',)
    
class FactAdmin(admin.ModelAdmin):
    list_display = ('fact_term',)

    fields = ('fact_term','fact_values','value_iobject_id','value_iobject_ts')

class Enrichment2FactAdmin(admin.ModelAdmin):
    pass


class RelationAdmin(admin.ModelAdmin):
    list_display = ('__unicode__',)

#
# Registration
# ------------
#
# Below, we register admin interfaces.
#

# Enumerables; useful for managing enumerables


admin.site.register(FactDataType,FactDataTypeAdmin)
admin.site.register(DataTypeNameSpace,NameSpaceAdmin)
admin.site.register(InfoObjectType,InfoObjectTypeAdmin)
admin.site.register(InfoObjectFamily,InfoObjectFamilyAdmin)
admin.site.register(FactTerm2Type,FactTerm2TypeAdmin)


# InfoObjects and Relations
# Admin interface for these objects is
#  moderately useful for viewing data
# (better use Dingo's Views for navigation)

admin.site.register(InfoObject,InfoObjectAdmin)
admin.site.register(Relation,RelationAdmin)


# Helper object: Admin interface useful for checking, debugging...

admin.site.register(FactTerm,FactTermAdmin)
admin.site.register(FactValue,FactValueAdmin)
admin.site.register(NodeID)
admin.site.register(Identifier,IdentifierAdmin)
admin.site.register(Fact,FactAdmin)
admin.site.register(InfoObject2Fact,InfoObject2FactAdmin)
admin.site.register(Revision)
admin.site.register(BlobStorage)



