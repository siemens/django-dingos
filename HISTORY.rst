.. :changelog:

History
-------

0.3.0
+++++

* Added custom queries

* Added framework for writing exporter function; these
  functions can be made available via the GUI as well
  as tied into the custom query as postprocessor.

* Add framework for extracting graph-information from
  database

* Add graph-display for InfoObjects and their relations

* Add framework for defining object-type-specific views

* Added capability to associate identifier namespaces
  with images and display images instead of textual
  namespace representation.

* Added basic view class for writing views that carry
  out bulk operations on InfoObjects with "attaching
  markings to selected objects" as special case.

* Add interface for managing OAuth keys

* Add hook to base import command

* Add dingos-specific definition of menu items

* Add Django 1.7 migrations



0.2.1 (2014-03-06)
++++++++++++++++++

* Bugfixes

  * *CRITICAL* Remediation of painfully slow import for systems with lot's of imported data

    An illformed query led to extremely slow import of new data in systems
    that already have lot's of data inside. This bug has been fixed.

  * Problem in link to InfoObjects in which a certain fact can be found on Unique Search Page fixed

    The link was faulty in that it carried a '&page=...' parameter that needed to be removed. 

  * Long repetition of '_' in a string lead to HTML display spilling over, because '_' was
    not regarded as place to insert a possible line break. This has been changed.
  
* New/Modified views

  * View for listing *all* InfoObjects, also those used internally by DINGOS
    for bookkeeping (e.g., user preferences). The view is restricted to
    Django-superusers.

* New/Modified command-line commands

  * In 'dingos_manage_user_settings', added the ability to overwrite settings for 'ALL'
    users.


0.2.0 (2014-02-24)
++++++++++++++++++

* New base functionality

  * Added framework for managing user-specific data (user configurations,
    saved searches, etc.) and querying user-specific data in templates and views.

  * Added tracking of namespace information per component of a fact term

* New/Modified views

  * Modifications to all views

    * Added possibility to switch between horizontal and vertical layout ...
      or have automatic adjustment of the layout depending on screen width.

  * Modifications to filter views

    * Modified date-picker in filters to enable addition of timespans without
      changing saved searches or messing up order of timespans

    * Added several further filter criteria in InfoObject filter

  * Added view with basic and still rather restricted editing capabilities for
    InfoObjects -- currently only used for editing user preferences or
    edits by the superuser

  * Added view to edit user configuration

  * Added view to edit saved searches

  * Added per-column ordering to list views

  * Added new filter/search that shows unique Facts rather than all
    InfoObjects containing a certain fact.

* New/added capabilities for writing views

  * Added framework for ordering list views

  * Added per-user configuration for:

    * layout (horizontal vs. vertical)
    * number of rows to show in list views
    * number of rows to show in widget displaying objects in which a
      displayed object is embedded

* Bug fixes / Improvements

  * Generation of filter views became unbearably slow when many
    (> 40,000) InfoObjects are in the system. This was, because
    of a badly built query within the dynamically built filter
    form. This has been fixed.

  * Further development of JSON export (still needs work to make
    the to_dict function of InfoObjects generic and configurable such as
    the from_dict function)

  * Fixed bug in generation of InfoObjects: when a placeholder for a given
    ID already existed, it was not reliably found.

* New/Modified command-line commands

  * Import command now fails gracefully if import of a file
    throws an exception: it continues with import of the next file.

  * Added command line arguments to basic import command:

    * ability to add IDs of marking objects to be added to imported objects

    * ability to automatically move imported XML files to other folder after
      import

  * Added command to reset user-settings and saved searches for a given user.

  * Added command to re-calculate object names.

    This is useful to run right after an import, recalculating the
    names of 'Observable' InfoObjects created in the past few minutes.  Thus, the
    problem that those Observables that are to be named after the (single)
    object they contain do not carry a proper name (because at creation time
    of the Observable, the Object usually does not exist, yet) can be fixed.


0.1.0 (2013-12-19)
++++++++++++++++++

* Bugfixes; added documentation

0.0.9 (2013-12-16)
++++++++++++++++++

* First release on PyPI.
