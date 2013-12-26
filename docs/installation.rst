============
Installation
============

#. Make sure that you have the required
   dependencies on OS level for building the XML-related packages. For
   example, on an Ubuntu system, execute the following commands::

     apt-get install libxml2 libxml2-dev
     apt-get install python-dev libxslt1-dev


#. Find out the current version of ``libxml2-python`` by browsing to
   https://pypi.python.org/pypi/libxml2-python and noting done the
   version number (at time of writing, this was ``2.6.21``).

#. Install ``django-dingos`` using ``pip``::

      $ pip install ftp://xmlsoft.org/libxml2/python/libxml2-python-<libxml2-python-version-nr>.tar.gz 
      $ pip install django-dingos

#. Add ``dingos`` and ``grappelli`` to your ``INSTALLED_APPS`` list in your settings.

#. To get started, add the ``dingos`` urls to your ``url.py`` like so::

          urlpatterns = patterns('',
                                 ...

                                 url(r'^dingos/', include('dingos.urls')),

				 ...)

#. Dingos uses the ``grappelli`` application (see `django-grappelli`_). This requires you to
   run the collect static command once after installing ``grappelli``::

     python manage.py collectstatic 



#. If you are using `south`_ (and you *should* be using *south*), carry out the schemamigration
   for dingos::

     python manage.py migrate dingos

   Otherwise (this is not recommended, because migrating to future releases of DINGOS will be a pain),
   run::

    python manage.py syncdb

.. _south: http://south.readthedocs.org/en/latest/

.. _django-grappelli: https://github.com/sehmaschine/django-grappelli
