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
    InfoObjectFamily,\
    Revision,\
    FactTerm2Type,\
    FactDataType,\
    InfoObjectType,\
    NodeID,\
    InfoObjectNaming,\
    BlobStorage,\
    IdentifierNameSpace



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


class DataTypeNameSpace_FactDataType_Inline(admin.TabularInline):
    model = FactDataType
    extra = 0
    fields=('name','description')
    readonly_fields = ('description',)






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

class FactDataTypeAdmin(admin.ModelAdmin):
    list_display = ('name','kind','namespace')
    raw_id_fields = ('namespace',)
    autocomplete_lookup_fields = {
        'fk': ['namespace'],
        'm2m': [],
    }


class DataTypeNameSpaceAdmin(admin.ModelAdmin):
    list_display = ('uri','name',)
    #filter_horizontal = ('factdatatype_set',)
    #inlines = (DataTypeNameSpace_FactDataType_Inline,)

class InfoObjectTypeAdmin(admin.ModelAdmin):
    list_display = ('name','iobject_family','namespace')
    inlines = (InfoObjectType_InfoObjectNaming_Inline,)

class FactTerm2TypeAdmin(admin.ModelAdmin):
    list_display = ('fact_term','iobject_type')
    raw_id_fields = ('iobject_type','fact_data_types')

    autocomplete_lookup_fields = {
        'fk': ['iobject_type',],
        'm2m': ['fact_data_types',],
        }



class InfoObjectFamilyAdmin(admin.ModelAdmin):
    list_display = ('name','title','description',)

class BlobStorageAdmin(admin.ModelAdmin):
    list_display = ('sha256',)

#
# Registration
# ------------
#
# Below, we register admin interfaces.
#

# Enumerables; useful for managing enumerables


admin.site.register(FactDataType,FactDataTypeAdmin)
admin.site.register(DataTypeNameSpace,DataTypeNameSpaceAdmin)
admin.site.register(IdentifierNameSpace)
admin.site.register(InfoObjectType,InfoObjectTypeAdmin)
admin.site.register(InfoObjectFamily,InfoObjectFamilyAdmin)
admin.site.register(FactTerm2Type,FactTerm2TypeAdmin)



# Helper object: Admin interface useful for checking, debugging...

admin.site.register(NodeID)
admin.site.register(Revision)
admin.site.register(BlobStorage,BlobStorageAdmin)



