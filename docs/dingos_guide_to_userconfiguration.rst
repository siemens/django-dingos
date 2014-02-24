Dingos User Configuration Facilities
====================================

Defining user configurations
----------------------------

The default user configuration is defined in the constant ``DINGOS_DEFAULT_USER_PREFS``.
``dingos/__init__.py`` but can be overwritten in the settings, e.g. as follows::


    DINGOS = {
              (...)
              'DINGOS_DEFAULT_USER_PREFS' : {
                  'dingos' : { 'widgets' :
                                   {'embedded_in_objects' :
                                        {'lines' : {'@description': """Max. number of objects displayed in
                                                            widget listing the objects in which the
                                                            current object is embedded.""",
                                                    '_value' : '5'}
                                        } ,
                                    },
                               'view' :
                                   {'pagination':
                                        {'lines' : {'@description': """Max. number of lines displayed in
                                                        paginated views.""",
                                                    '_value' : '20'},
                                         },
                                    'orientation' : {'@description': """Layout orientation. Possible values are 'vertical', 'horizontal', and 'auto'.""",
                                                     '_value' : 'horizontal'}
                                   }
    
                  }
              }

     (...)
    }


When a user logs in for the first time, the standard user configuration is copied over to his personal
user configuration. The user configuration can be viewed with the view named ``url.dingos.admin.view.userprefs`` --
the standard URL for this view is ``../Admin/ViewUserPrefs``.

A logged in user can edit the settings under the ``ViewUserPrefs``.
Alternatively, for testing purposes, you can change the preferences
via the command line interface::

    python manage.py dingos_manage_user_settings --reset preferences <user_name1> <user_name2> --settings=...

After doing this, go to the above-mentioned view of the user preferences for a user to also refresh the user data that has
been cached in the session.

Accessing user configurations in templates
------------------------------------------

In templates, user configurations are accessed as follows::

    customization.<default_value>.<path>.<to>.<value>.<in>.<config>.<dictionary>

For example to access the orientation of the display defined as ``horizontal``
above, you would write::

    customization.horizontal.dingos.view.orientation

Or, to access the number of lines to be shown on a list display (with a default value of `15`),
you would write::

    customization.15.dingos.view.pagination.lines

Accessing user configuration in views
-------------------------------------

The Dingos standard views all include the mixin ``ViewMethodsMixin``,
which defines the function ``lookup_customization``. In order to look
up the number of lines to be shown on a list display (with a
default value of `15`), you would write::

    self.lookup_customization('dingos','view','pagination','lines',default=15)




