Writing views and templates for Dingos
======================================

.. contents::

Relevant folders and files
--------------------------

Templates
.........

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


Views
.....

DINGOS makes extensive use of Django's class-based views. In ``view_classes.py``,
we define mixins and base classes that are used for defining views
in DINGOS; the views themselves are defined in ``views.py``.

Supporting Documentation
------------------------

- For basics on templates, refer to the `Django documentation on the template language`_.
- In order  to learn how to use the `Django Grappelli`_ CSS, make sure to include
  ``(r'^grappelli/', include('grappelli.urls'))`` in your url patterns in ``url.py``.
  You can then view the Grappelli CSS documentation under ``<your Django server url>/grappelli/grp-doc/``.
- For information on class-based views see:
  - `Django documentation on class-based views`_
  - `Django documentation on using mixins in class-based views`_

Dingos-specific features
------------------------


User configurations
...................

Since Dingos 0.1.1, Dingos offers resources for structured management of user-specific
data such as user-configurations. Please refer to :doc:`dingos_guide_to_userconfiguration` for
more information.


Tips and tricks
---------------

When writing and testing views, do not even start without the excellent `Django Debug Toolbar`_:
it shows you, for example, how many which SQL queries were executed (which will help you
to find the right configuration for the `prefetch_related`_ and `select_related`_



.. _Django documentation on custom django-admin commands: https://docs.djangoproject.com/en/dev/howto/custom-management-commands/

.. _Django documentation on the template language: https://docs.djangoproject.com/en/dev/topics/templates/

.. _Django Grappelli: https://django-grappelli.readthedocs.org/en/latest/

.. _Django documentation on the admin site: https://docs.djangoproject.com/en/dev/ref/contrib/admin/

.. _django-filter: https://django-filter.readthedocs.org/en/latest/

.. _django-filter documentation: https://django-filter.readthedocs.org/en/latest/

.. _Django documentation on the URL dispatcher: https://docs.djangoproject.com/en/dev/topics/http/urls/

.. _Django documentation on class-based views: https://docs.djangoproject.com/en/dev/topics/class-based-views/

.. _Django documentation on using mixins in class-based views: https://docs.djangoproject.com/en/dev/topics/class-based-views/mixins/

.. _Django Debug Toolbar: https://github.com/django-debug-toolbar/django-debug-toolbar

.. _prefetch_related: https://docs.djangoproject.com/en/dev/ref/models/querysets/#prefetch-related

.. _select_related: https://docs.djangoproject.com/en/dev/ref/models/querysets/#select-related



