"""
Defines a BoundWorld - a convience class that organises ECS function calls.
"""
from typing import Optional
from functools import partial

import snecs.ecs
from snecs.query import Query
from snecs.world import World

__all__ = ["BoundWorld"]


class BoundWorld(World):
    """A World class with bound methods."""

    __slots__ = (
        "new_entity",
        "add_component",
        "add_components",
        "entity_component",
        "entity_components",
        "all_components",
        "has_component",
        "has_components",
        "remove_component",
        "schedule_for_deletion",
        "exists",
        "delete_entity_immediately",
        "process_pending_deletions",
        "query",
    )

    def __init__(self, name: Optional[str] = None) -> None:
        super().__init__(name)
        ecs = snecs.ecs
        self.new_entity = partial(ecs.new_entity, world=self)
        self.add_component = partial(ecs.add_component, world=self)
        self.add_components = partial(ecs.add_components, world=self)
        self.entity_component = partial(ecs.entity_component, world=self)
        self.entity_components = partial(ecs.entity_components, world=self)
        self.all_components = partial(ecs.all_components, world=self)
        self.has_component = partial(ecs.has_component, world=self)
        self.has_components = partial(ecs.has_components, world=self)
        self.remove_component = partial(ecs.remove_component, world=self)
        self.schedule_for_deletion = partial(
            ecs.schedule_for_deletion, world=self
        )
        self.exists = partial(ecs.exists, world=self)
        self.delete_entity_immediately = partial(
            ecs.delete_entity_immediately, world=self
        )
        self.process_pending_deletions = partial(
            ecs.process_pending_deletions, world=self
        )
        self.query = partial(Query, world=self)
