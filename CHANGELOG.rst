.. _snecs_changelog:

=========
Changelog
=========

v1.1.0
======

Changes/Fixes
-------------

* ``serialize_world`` and ``deserialize_world`` now use strings as the
  dictionary keys, to permit using JSON as an interchange format.

v1.0.0
======

Fixes
-----

- Fixed a critical bug that caused ``process_pending_deletions`` to never
  actually remove the entities from the deletion queue, thus making every
  subsequent call fail.

- Fixed a critical bug in ``register_component`` that prevented actually
  implementing ``Component.serialize`` and ``Component.deserialize``, because
  it never detected a class as overriding ``deserialize``.

- Fixed another critical bug in ``register_component`` that prevented
  Component names being registered, and so made it impossible to deserialize
  a World.

Changes
-------

- ``World.__init__()`` now accepts an optional ``name`` argument.

  Named worlds can be looked up by name when an explicit reference to them is
  not available, using the new class method ``World.get_by_name(name)``.

  The name is used in ``__repr__``.

- The ``world`` argument to `process_pending_deletions`, `serialize_world`,
  and `deserialize_world` is now optional with a default of the default_world.

  This is to bring those functions in-line with all the other ones, and
  allow full "``World()``-less" usage of ``snecs``.


Backwards-incompatible Changes
------------------------------

- Renamed ``snecs.types`` to ``snecs.typedefs`` to avoid name clashes with
  the standard library module ``types``.

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
