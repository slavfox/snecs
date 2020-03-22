.. _api_reference:

=============
API Reference
=============

All the public classes and functions exposed by ``snecs`` are documented here.
Here's a handy list of the individual sections:

- `snecs.world`_
- `snecs.component`_
- `snecs.ecs`_
- `snecs.types`_

.. _snecs.world:

snecs.world
===========

.. automodule:: snecs.world
   :members:

.. _snecs.component:

snecs.component
===============

.. automodule:: snecs.component
   :members:

.. _snecs.ecs:

snecs.ecs
=========

.. automodule:: snecs.ecs
   :members:

.. _snecs.types:

snecs.types
===========

``snecs`` is fully type hinted and checked with mypy_. The ``snecs.types``
module exports a couple types you might need if you want to type hint the
parts of your code that use ``snecs``:

.. _mypy: http://mypy-lang.org/

.. class:: snecs.types.EntityID([int])

   A subclass of ``int`` (effectively a `typing.NewType("EntityID", int)
   <typing.NewType>`) used for annotating entity identifiers. At runtime,
   exactly equivalent to ``int``.

   All the functions in ``snecs`` that take an entity ID as an argument or
   return one are annotated appropriately with ``EntityID``.

.. class:: snecs.types.SerializedWorldType

   This constant defines the exact return type of `snecs.ecs.serialize_world`.
   It exists as an alias so that your typed code doesn't need to specify the
   type literally - to make migration easier when PyPy 3.8 releases with
   `typing.TypedDict`.

.. class:: snecs.types.QueryType

   The abstract base class for all `queries <query>`::

       def execute_query(q: QueryType) -> ...:
           ...

       my_query = query([MyComponent])
       compiled = my_query.compile()

       execute_query(my_query)  # ok!
       execute_query(compiled)  # ok!
       execute_query(MyComponent)  # error!

   .. note::

      You can also use ``query`` itself as a type annotation, but remember
      that compiled queries aren't a subclass of ``query``::

           def compile_query(q: query) -> ...:
               ...

           my_query = query([MyComponent])
           compiled = my_query.compile()

           compile_query(my_query)  # ok!
           compile_query(compiled)  # error!

.. class:: snecs.types.CompiledQueryType

   The abstract base class for all *compiled* queries::

       def execute_compiled_query(q: CompiledQueryType) -> ...:
           ...

       my_query = query([MyComponent])
       compiled = my_query.compile()

       execute_compiled_query(my_query)  # error!
       execute_compiled_query(compiled)  # ok!

.. class:: snecs.types.Expr

   The abstract base class for `filter expressions`::

       def foo(e: Expr) -> ...:
           ...

       # `ComponentA & ComponentB` and all other filter expressions are of
       # type `Expr`.
       foo(ComponentA & ComponentB)  # ok!
       foo(~ComponentC | (ComponentA & Component))  # ok!

       # `ComponentA` is of type `Type[Component]`
       foo(ComponentA)  # error!

   Note that filter expressions accept lone component types - the type of
   "any value accepted by `query.filter`" is
   ``Union[Expr, Type[Component]]``.
