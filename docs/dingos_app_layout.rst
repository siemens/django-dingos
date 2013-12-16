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
     │   ├── import_handling.py
     │   ├── importer.py
     │   ├── models.py
     │   ├── __init__.py
     │   ├── read_settings.py
     │   ├── urls.py
     │   ├── view_classes.py
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

DINGOS uses Django templates (see `Django documentation on the template language`_)
for rendering HTML pages. These are located in the ``template\dingos\grappelli`` folder.
The reason for this nesting is the following:

* by having ``dingos`` in the file path, also other apps are able to refer to templates
  defined in DINGOS
* by having ``grappelli`` in the file path, we are open to supporting different CSS frameworks
  at a later point of time: for supporting, e.g., ``bootstrap``, a folder ``templates\bootstrap``
  would have to be added and would then contain the bootstrap-based templates.

In order  to learn how to use the `Django Grappelli`_ CSS, make sure to include
``(r'^grappelli/', include('grappelli.urls'))`` in your url patterns in ``url.py``.
You can then view the Grappelli CSS documentation under ``<your Django server url>/grappelli/grp-doc/``.

``templatetags\dingos_tags.py``
-------------------------------

When you are viewing a template and find something like ``{% show_InfoObjectIDData object %}`` that
seems to do something magical (in this case, rendering a box containg identifier data of an object),
then you are looking at a Django /template tag/. Those are defined in ``templatetags\dingos_tags.py``;
the template snippets used by the tags are defined in ``templates\dingos\grappelli\includes`.

``admin.py``
------------

Configuration for the Django admin interface: via the admin interface, you can access the
DINGOS models. That is useful for viewing certain data (e.g., which namespaces do I have
in my system?) and configuring data (e.g., managing naming schemas via the ``InfoObjectType``
objects). Refer to the `Django documentation on the admin site`_ for details about
the contents of ``admin.py`` -- you may also want to have a look at
the documentation of `Django Grappelli`_, since ``admin.py`` uses some extensions
provided by Grappelli.

``filter.py``
-------------

DINGOS uses the `django-filter`_ app to generate filters for list views. The 
configuration for the filters is located in ``filter.py``: for background on
how to configure filters, please refer to the `django-filter documentation`_.

``import_handling.py``
----------------------

Next to ``models.py`` (see below), this is the heart of DINGOS: it defines the
class ``DingoImportHandling`` that contains the ``xml_import`` function,
a highly configurable function for turning XML into DINGOS dictionary objects,
and ``create_iobject``, the function used to write a DINGOS dictionary object
to a ``InfoObject`` in the database.

``importer.py``
---------------

The most important content of this file is the generic class ``DingoImportCommand``
which provides the basis for easy implementation of import scripts to
be carried out via the command-line (see above under ``management/commands``
and `Django documentation on custom django-admin commands`_.

This file also contains a very simple generic XML importer, which is mostly for
demonstration purposes. 

``models.py``
-------------

The heart of DINGOS. The code is extensively documented; please refer to the
:download:`DINGOS Developers' Overview <reference/dingos_data_model.pdf>` of the DINGOS models
for an overview.

``__init__.py``
---------------

DINGOS uses the ``__init__.py`` file to define a number of defaults used
within the DINGOS code.

``read_settings.py``
--------------------

Code for reading DINGOS-specific settings configured in the Django settings
file(s). Some of the defaults defined in ``__init__.py`` can be 
overwritten here. 


``urls.py``
-----------

The Django URL configuration. See the `Django documentation on the URL dispatcher`_.

``view_classes.py``
-------------------

DINGOS makes extensive use of Django's class-based views (see the
`Django documentation on class-based views`_). In ``view_classes.py``,
we define mixins (see also the `Django documentation on using mixins in class-based views`_) 
and base classes that are used for defining views
in DINGOS.

``views.py``
------------

The DINGOS views. Refert to the
`Django documentation on class-based views`_.






.. _Django documentation on custom django-admin commands: https://docs.djangoproject.com/en/1.6/howto/custom-management-commands/

.. _Django documentation on the template language: https://docs.djangoproject.com/en/dev/topics/templates/

.. _Django Grappelli: https://django-grappelli.readthedocs.org/en/latest/

.. _Django documentation on the admin site: https://docs.djangoproject.com/en/1.6/ref/contrib/admin/

.. _django-filter: https://django-filter.readthedocs.org/en/latest/

.. _django-filter documentation: https://django-filter.readthedocs.org/en/latest/

.. _Django documentation on the URL dispatcher: https://docs.djangoproject.com/en/dev/topics/http/urls/

.. _Django documentation on class-based views: https://docs.djangoproject.com/en/dev/topics/class-based-views/

.. _Django documentation on using mixins in class-based views: https://docs.djangoproject.com/en/dev/topics/class-based-views/mixins/
