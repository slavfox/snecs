"""
Query builder.
"""
from typing import TYPE_CHECKING, Iterable, Iterator
from abc import ABC, abstractmethod

from snecs.filters import compile_filter, matches
from snecs.world import default_world

if TYPE_CHECKING:
    from typing import Tuple, Optional, Type, List, TypeVar, AbstractSet
    from snecs.component import Component
    from snecs.world import World, EntityID
    from snecs.filters import Term, CompiledFilter

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
    set_intersection = frozenset().intersection


class BaseQuery(Iterable["QueryRow"], ABC):
    __slots__ = ("world", "component_types")

    def __init__(
        self,
        component_types: "Iterable[Type[Component]]",
        world: "World" = default_world,
    ) -> "None":
        self.world = world
        self.component_types: "Iterable[Type[Component]]" = component_types

    @abstractmethod
    def __iter__(self) -> "QueryIterator":
        ...


class CompiledQuery(BaseQuery, ABC):
    __slots__ = ()


class CompiledFilterQuery(CompiledQuery):
    __slots__ = ("_filter",)

    def __init__(
        self,
        component_types: "Iterable[Type[Component]]",
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
            *[entcache[ct] for ct in self.component_types]
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
            *[entcache[ct] for ct in self.component_types]
        )
        entities = self.world._entities
        cmptypes = self.component_types
        for entid in valid_entities:
            entcmps = entities[entid]
            yield entid, [entcmps[c] for c in cmptypes]


class query(BaseQuery):
    __slots__ = ("_filters",)

    def __init__(
        self,
        component_types: "Iterable[Type[Component]]",
        world: "World" = default_world,
    ) -> "None":
        super().__init__(component_types, world)
        self._filters: "Optional[Term]" = None

    def filter(self: "DQ", expr: "Term") -> "DQ":
        oldfilter = self._filters
        if oldfilter is None:
            self._filters = expr
        else:
            self._filters = oldfilter & expr
        return self

    def compile(self) -> "CompiledQuery":
        if self._filters is None:
            return CompiledRawQuery(self.component_types, world=self.world)
        return CompiledFilterQuery(
            self.component_types, compile_filter(self._filters), self.world
        )

    def __iter__(self) -> "QueryIterator":
        entcache = self.world._entity_cache
        valid_entities: "AbstractSet[EntityID]" = set_intersection(
            *[entcache[ct] for ct in self.component_types]
        )
        flt = self._filters
        entmasks = self.world._entity_bitmasks
        entities = self.world._entities
        cmptypes = self.component_types
        if flt is not None:
            for entid in valid_entities:
                if matches(flt, entmasks[entid]):
                    entcmps = entities[entid]
                    yield entid, [entcmps[c] for c in cmptypes]
        else:
            for entid in valid_entities:
                entcmps = entities[entid]
                yield entid, [entcmps[c] for c in cmptypes]
