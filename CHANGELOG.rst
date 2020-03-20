=========
Changelog
=========

Unreleased
==========

Backwards-incompatible Changes
------------------------------

- Moved `EntityID` to ``snecs.types``.

  This prevents the obscure scenario where PyCharm suggests to a user to
  import the name from where all the ``snecs`` code imports it from (which
  was, previously, ``_detail``) and then screeches about accessing private
  submodules.

- Renamed ``query`` to `Query`.

  ``query`` was far too handy of a name for a variable for ``snecs`` to
  force its users to use something else.

0.2.0 (2020-03-20)
==================

Changes
-------

- Fixed the accidental use of ``set().intersection(*sets)`` rather than
  ``set.intersection(*sets)`` that prevented multi-component queries from
  ever returning any results.
