.. _ECS:

==============
What's an ECS?
==============

*"ECS"* stands for `Entity-Component-System`_. It's a software architecture
pattern gaining increasing popularity in video game development in recent
years, as a `data-oriented`_ alternative to classic object-orientation. It
makes a lot of sense in low-level languages like Rust or C, since it immensely
helps to improve data locality - and thus performance. Nevertheless, the clean,
easy-to-understand design that results from mindful use of an ECS architecture
appeals even to users of very-high-level languages, as can be seen by the
popularity of projects like the ClojureScript Chocolatier_, Mozilla's ecsy_,
or the pure-Python, roughly 300-line esper_.

In short, in an ECS architecture, your code doesn't operate on complex
objects, built out of big pyramids of inheritance, methods, protocols, and
interfaces. Instead, every object in your game - an **Entity** - is
represented by only a plain, unique numeric identifier. As far as your code is
concerned, an entity is just ``23`` or ``42`` or ``2766``.

.. note::

    If you're familiar with relational databases, you can think of entity IDs
    as the primary key for a table of entities, where each record is just
    foreign keys to tables representing individual Components.

Useful information that can be acted upon by your code is added to entities
with **Components**. A component, in ECS, is just a simple piece of data,
without any behaviors attached to it. Some examples of components would be
structures like ``Position``, ``Sprite``, ``Stats``. A component may hold
no data whatsoever - like a ``OnFireStatusEffect`` component, when we're
only interested in whether an entity is on fire (has that component) or not
(does not have that component) - or it may hold arbitrarily structured and
complex data. It all depends on how you want to use them!

To actually add behaviors to Components, we use **Systems**. A System
is nothing more than a function that runs in a loop, and processes all the
entities and components it's interested in. Here are some ``snecs`` examples
of Systems::

    def process_movement():
        for entity, (position, velocity) in query(
            (Position, Velocity)
        ):
            position.x += velocity.x
            position.y += velocity.y

    def process_drawables():
        for entity, (position, drawable) in query(
            (Position, Drawable)
        ):
            draw_to_screen(drawable, position=position)


Proceed to :ref:`getting_started` when you're ready to explore the ECS
pattern with ``snecs``!

.. _Entity-Component-System: https://en.wikipedia.org/wiki/Entity_component_system
.. _data-oriented: https://en.wikipedia.org/wiki/Data-oriented_design
.. _Chocolatier: https://github.com/alexkehayias/chocolatier
.. _ecsy: https://ecsy.io/
.. _esper: https://github.com/benmoran56/esper.git
