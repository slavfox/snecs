"""
Query builder.
"""
from typing import TYPE_CHECKING, Iterable, Iterator
from abc import ABC, abstractmethod

from snecs._filters import compile_filter, matches
from snecs.world import default_world

if TYPE_CHECKING:
    from typing import (
        Tuple,
        Optional,
        Type,
        List,
        TypeVar,
        AbstractSet,
        Collection,
    )
    from snecs.component import Component
    from snecs.world import EntityID, World
    from snecs._filters import Term, CompiledFilter

    QueryRow = Tuple[EntityID, List[Component]]
    QueryIterator = Iterator[QueryRow]
    DQ = TypeVar("DQ", bound="query")

    T = TypeVar("T")

    def set_intersection(
        *s: "AbstractSet[EntityID]",  # noqa
    ) -> AbstractSet[EntityID]:
        ...


else:
    # get rid of the attribute lookup for performance
    set_intersection = set.intersection


__all__ = ["query"]

_EMPTY_SET: "AbstractSet[EntityID]" = frozenset()


class BaseQuery(Iterable["QueryRow"], ABC):

    __slots__ = ("world", "component_types")

    def __init__(
        self,
        component_types: "Collection[Type[Component]]",
        world: "World" = default_world,
    ) -> "None":
        self.world = world
        self.component_types: "Collection[Type[Component]]" = component_types

    @abstractmethod
    def __iter__(self) -> "QueryIterator":
        ...


class CompiledQuery(BaseQuery, ABC):
    """
    Base class for compiled queries. See `query.compile`.

    Compiled queries are not filterable further. Filter them before
    compilation!
    """

    __slots__ = ()


class CompiledFilterQuery(CompiledQuery):
    """
    A compiled query with filters.

    The filters get compiled to a very fast expression; filtering a
    non-compiled, dynamic query is O(n), where ``n`` is the number of
    individual expressions in the filters (eg. ``A & B`` is three expressions
    - first matching against ``A``, then against ``B``, and then taking the
    ``and`` of the two results).

    A compiled filter, on the other hand, is O(n), but where (n) is the
    number of ``or`` expressions specifically. A compiled ``A & B & ~C & ...``
    takes the same amount of time (slightly less, even) to check as a
    dynamic ``A``.
    """

    __slots__ = ("_filter",)

    def __init__(
        self,
        component_types: "Collection[Type[Component]]",
        filter_: "CompiledFilter",
        world: "World" = default_world,
    ) -> "None":
        self._filter = filter_
        super().__init__(component_types, world)

    def __iter__(self) -> "QueryIterator":
        # The body of this method is mostly duplicated in every Query
        # subclass for performance.
        # Python, pls add macros. I want macros. Stringy codegen is a pain.
        entcache = self.world._entity_cache
        # list comprehensions are faster than generators if we don't need to
        # have an early exit.
        valid_entities: "AbstractSet[EntityID]" = set_intersection(
            *[entcache.get(ct, _EMPTY_SET) for ct in self.component_types]
        )
        # Moving attributes into the local scope to avoid doing attribute
        # lookups in a loop
        fits = self._filter.matches
        entmasks = self.world._entity_bitmasks
        entities = self.world._entities
        cmptypes = self.component_types
        for entid in valid_entities:
            if fits(entmasks[entid]):
                entcmps = entities[entid]
                yield entid, [entcmps[c] for c in cmptypes]


class CompiledRawQuery(CompiledQuery):
    __slots__ = ()

    def __iter__(self) -> "QueryIterator":
        entcache = self.world._entity_cache
        valid_entities: "AbstractSet[EntityID]" = set_intersection(
            *[entcache.get(ct, _EMPTY_SET) for ct in self.component_types]
        )
        entities = self.world._entities
        cmptypes = self.component_types
        for entid in valid_entities:
            entcmps = entities[entid]
            yield entid, [entcmps[c] for c in cmptypes]


class query(BaseQuery):
    """
    An expression for querying the world for entities and Components.

    A query is instantiated by passing in a collection of component types to
    match, and is iterable, returning an iterator over tuples of
    ``(EntityId, List[Component])``.

    For instance, if you instantiate a query as::

        my_query = query((ComponentA, ComponentB))

    You can iterate over the results with::

        for entity_id, (component_a, component_b) in my_query:
            ...

    Note that the component types passed in at instantiation have to all be
    present on an entity, and will be included in the result. If you want to
    filter the query further, or want some of the components to not be
    returned, ``snecs`` overloads the three basic boolean operators on
    Component subclasses to let you filter queries in an expressive way::

        query(Position).filter((Velocity | Acceleration) & ~Frozen)

    The above query will return the entity_id and Position component for all
    entities that have a Position, are not Frozen, and have a Velocity or
    Acceleration (or both).
    """

    __slots__ = ("_filters",)

    def __init__(
        self,
        component_types: "Collection[Type[Component]]",
        world: "World" = default_world,
    ) -> "None":
        super().__init__(component_types, world)
        self._filters: "Optional[Term]" = None

    def filter(self: "DQ", expr: "Term") -> "DQ":
        """
        Filter this query according to a filter expression.
        """
        oldfilter = self._filters
        if oldfilter is None:
            self._filters = expr
        else:
            self._filters = oldfilter & expr
        return self

    def compile(self) -> "CompiledQuery":
        """
        Compile this query into a much faster one.

        This brings a big performance gain when using filters, and a
        negligible one (but still a performance gain, nevertheless) with
        unfiltered queries.

        Queries are intended to be compiled outside the hot path, like so::

            # compiled when the file is processed (imported)
            momentum_query = query((Position, Velocity), MY_WORLD).compile()

            def process_momentum():
                for entity, (Position, Velocity) in momentum_query:
                    ...
        """
        if self._filters is None:
            return CompiledRawQuery(self.component_types, world=self.world)
        return CompiledFilterQuery(
            self.component_types, compile_filter(self._filters), self.world
        )

    def __iter__(self) -> "QueryIterator":
        """
        Iterate over the results of this query.

        This does most of the heavy lifting before the actual loop, by taking
        an intersection of the sets of entities that have a specific
        component for each of the components we're querying for.
        """
        entcache = self.world._entity_cache
        cmptypes = self.component_types
        fst, *rest = cmptypes
        if rest:
            valid_entities: "AbstractSet[EntityID]" = set_intersection(
                *[entcache.get(ct, _EMPTY_SET) for ct in cmptypes]
            )
        else:
            # elide the set intersection if we don't need to do it
            valid_entities = entcache.get(fst, _EMPTY_SET)
        flt = self._filters
        entities = self.world._entities
        # If this query is filtered, match against each result individually.
        if flt is not None:
            entmasks = self.world._entity_bitmasks
            for entid in valid_entities:
                if matches(flt, entmasks[entid]):
                    entcmps = entities[entid]
                    yield entid, [entcmps[c] for c in cmptypes]
        # If not, just yield the results.
        else:
            for entid in valid_entities:
                entcmps = entities[entid]
                yield entid, [entcmps[c] for c in cmptypes]
