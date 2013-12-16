DINGOS Application Layout
=========================


The layout of the DINGOS Django application is as follows::

     .
     ├── dingos
     │   ├── core
     │   │   ├── datastructures.py
     │   │   └── ...
     │   ├── management
     │   │   └── commands
     │   │       └── dingos_generic_xml_import.py
     │   │       
     │   ├── migrations
     │   │   ├── 0001_initial.py
     │   │   └── ...
     │   ├── templates
     │   │   └── dingos
     │   │       └── grappelli
     │   │           ├── base.html
     │   │           ├── details
     │   │           │   └── ...
     │   │           ├── includes
     │   │           │   └── ...
     │   │           ├── lists
     │   │           │   └── ...
     │   │           └── searches
     │   │               └── ...
     │   ├── templatetags
     │   │   └── dingos_tags.py
     │   ├── admin.py
     │   ├── filter.py
     │   ├── importer.py
     │   ├── import_handling.py
     │   ├── models.py
     │   ├── read_settings.py
     │   ├── urls.py
     │   ├── view_classes.py
     │   ├── view_classes.pyc
     │   └── views.py


``core``: internal DINGOS libraries
-----------------------------------

Internal libraries with helper functions are placed in the ``core``
folder. The most important library probably is ``core/datastructures.py``,
which contains ``DingosObjDict``, the dictionary structure into which
imported data is written.  ``DingosObjDict`` preserves the order in
which keys have been added and knows how to /flatten/ itself into
a list of facts.

``management/commands``
-----------------------

This folder contains code for the command-line scripts that
can be executed via Django's ``django-admin`` or ``manage.py``
interface. Refer to `Django documentation on custom django-admin commands`_
for a description of how commands can be added.

``templates\dingos\grappelli``
------------------------------




.. _Django documentation on custom django-admin commands: https://docs.djangoproject.com/en/1.6/howto/custom-management-commands/

