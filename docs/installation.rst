============
Installation
============

#. Install ``django-dingos`` using ``pip``::

      $ pip install django-dingos

   If installation via ``pip`` fails, make sure that you have the required
   dependencies on OS level for building the XML-related packages. For
   example, on an Ubuntu system, execute the following commands::
     apt-get install libxml2 libxml2-dev
     apt-get install python-dev libxslt1-dev

#. Dingos uses the ``grappelli`` application. You therefore have to add 
   ``grappelli`` to your ``INSTALLED_APPS`` list in your settings and run
   the collect static command::

     python manage.py collectstatic 


#. Add ``dingos`` to your ``INSTALLED_APPS`` list in your settings.

