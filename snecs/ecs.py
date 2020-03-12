"""
Functions for interacting with the ECS.
"""
from typing import TYPE_CHECKING
from types import MappingProxyType

from snecs._detail import ZERO
from snecs.component import _component_registry
from snecs.world import default_world

if TYPE_CHECKING:
    from typing import Type, Iterable, TypeVar, Mapping
    from snecs.component import Component
    from snecs.world import World, EntityID

    C = TypeVar("C", bound=Component)

__all__ = [
    "new_entity",
    "add_components",
    "entity_component",
    "entity_components",
]


def new_entity(
    components: "Iterable[Component]" = (), world: "World" = default_world
) -> "EntityID":
    """
    Create an entity in a `World` with the given Components, returning its ID.

    :param world: World to create the entity in.
    :param components: An iterable of `Component` instances to attach to the
                       entity.
    :return: ID of the newly created entity.
    """
    id_ = world._entity_counter = world._entity_counter + 1
    bitmask = ZERO
    entdict = {}
    for component in components:
        cc = component.__class__
        bitmask |= _component_registry[cc]
        entdict[cc] = component
    world._entities[id_] = entdict
    world._entity_bitmasks[id_] = bitmask
    return id_


def add_components(
    entity_id: "EntityID",
    components: "Iterable[Component]",
    world: "World" = default_world,
) -> "None":
    """
    Add components to an entity.

    Will throw KeyError if the `Component` type was not registered using
    `register_component`, or if the entity doesn't exist in the given `World`.

    :param entity_id: ID of the entity to add the Components to.
    :param components: An iterable of Component instances to add to the Entity.
    :param world: The World holding the entity.
    """
    entity = world._entities[entity_id]
    if __debug__:
        common = world._entities.keys() & {c.__class__ for c in components}
        if common:
            raise AssertionError(
                f"Entity ID {entity_id} already has the following "
                f"components: {common}. Adding multiple components of the "
                f"same type to the same entity is not allowed."
            )
    new_bitmask = ZERO
    for c in components:
        cc = c.__class__
        new_bitmask |= _component_registry[cc]
        entity[cc] = c
    world._entities[entity_id].update({c.__class__: c for c in components})


def entity_component(
    entity_id: "EntityID",
    component_type: "Type[C]",
    world: "World" = default_world,
) -> "C":
    """
    Get the `Component` instance of a given type for a specific entity.

    Will throw a KeyError if the entity doesn't have a Component of the
    given type, or if the entity doesn't exist in this `World`.

    :param entity_id: Entity ID
    :param component_type: Type of the component to fetch
    :param world: The `World` to query
    :return: Component instance
    :raises KeyError: if the entity doesn't exist in this `World`.
    """
    return world._entities[entity_id][component_type]  # type: ignore
    # I know better.


def entity_components(
    entity_id: "EntityID", world: "World" = default_world
) -> "Mapping[Type[Component], Component]":
    """
    Get a mapping of all Components for a specific entity in a given World.

    Will throw a KeyError if the entity doesn't exist in this `World`.

    :param entity_id: Entity ID
    :param world: The `World` to query
    :return: An immutable mapping between each Component type of which the
             entity has an instance, and the instance.
    :raises KeyError: If the entity doesn't exist in this `World`.
    """
    return MappingProxyType(world._entities[entity_id])


def has_component(
    entity_id: "EntityID",
    component_type: "Type[Component]",
    world: "World" = default_world,
) -> "bool":
    """
    Check if a given entity has a specific `Component`.

    Will throw a KeyError if the entity doesn't exist in this `World`.

    ::
        if not has_component(entity_id, FreezeStatus):
            do_stuff(entity_id)

    :param entity_id: ID of the entity to check
    :param component_type: Component type to check
    :param world: World to check for the entity
    :return: bool
    :raises KeyError: If the entity doesn't exist in this `World`.
    """
    return component_type in world._entities[entity_id]


#
# def delete_entity(
#     entity_id: "EntityID",
#     world: "World" = default_world,
#     now: "bool" = False
# ) -> "None":
#     """
#     Schedule an entity for deletion from the World.
#
#     :param entity_id:
#     :param world:
#     :param now: If True, delete the entity immediately.
#     """
