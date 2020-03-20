.. _getting_started:

===============
Getting started
===============

First steps
===========

**The central object in** ``snecs`` **is a** ``World``.

A ``World`` is an opaque repository of all the data flowing through ``snecs``.
All the functions that let you interact with the library take an optional
``world`` argument.

If you're only ever using one ``World``, you don't actually need to
instantiate or pass it to functions explicitly - if you omit the ``world``
argument, ``snecs`` will use a default one. If you want to use more than one
``World`` in your code, you can create a new one just by::

    from snecs import World

    my_world = World()

You'd then pass ``my_world`` around explicitly to each function, by calling
them with ``world=my_world``.

Once you have a ``World``, the next step is adding some entities to it::

    from snecs import new_entity

    new_id = new_entity()
    # or, if you want to use a different world than the default:
    new_id = new_entity(world=my_world)

`new_entity` returns an integer [1]_, uniquely identifying the newly created
entity in that specific ``World``.

Entities without components are not very useful, though, and you'll probably
want to add some data do them. You can do that by subclassing `Component`::

    from snecs import Component, register_component

    @register_component
    class Position(Component):
        def __init__(self, x, y):
            self.x = x
            self.y = y

All ``Component`` classes that you intend to instantiate **must** be
registered by decorating them with `register_component` [2]_. Otherwise,
``snecs`` won't know about them!




Footnotes
=========


.. [1]

    If you're using mypy_ and `typing`, you may want to use `EntityID`
    from the :ref:`snecs.types` module for your type annotations - it's the
    return type of all the ``snecs`` functions that return... well, an entity
    ID. It is defined as an integer subtype, which strengthens the type safety
    a bit by forbidding most numeric operations on entity IDs.
    ``entity_id * 2`` is pretty meaningless, after all!

    If you're not using typing, just treat all entity IDs as a normal ``int``.

.. _mypy: http://mypy-lang.org/


.. [2]

    ``snecs`` also has a convenience class, `RegisteredComponent`, which
    automatically registers all its subclasses (and their subclasses!), so
    that you can avoid having to type ``@register_component`` over and over::

        from snecs import RegisteredComponent

        class Position(RegisteredComponent):
            def __init__(self, x, y):
                self.x = x
                self.y = y

    You shouldn't use it for classes that are abstract or have abstract
    subclasses.

    ``RegisteredComponent`` is also usable as a mixin::

        from abc import ABC
        from snecs import RegisteredComponent, Component

        class BaseComponent(Component, ABC):
            ...

        class ConcreteComponent(BaseComponent, RegisteredComponent):
            ...
