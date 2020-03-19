"""
Functions for interacting with the ECS.
"""
from typing import TYPE_CHECKING, cast
from types import MappingProxyType

from snecs._detail import ZERO
from snecs.component import _all_components_serializable, _component_names
from snecs.world import World, default_world

if TYPE_CHECKING:
    from typing import Type, Iterable, TypeVar, Mapping, Dict, Any, List
    from snecs.component import Component
    from snecs._detail import EntityID

    C = TypeVar("C", bound=Component)

__all__ = [
    "add_component",
    "add_components",
    "entity_component",
    "entity_components",
    "has_component",
    "has_components",
    "remove_component",
    "delete_entity",
    "delete_entity_immediately",
    "process_pending_deletions",
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
    if __debug__:
        unique_ctypes = {c.__class__ for c in components}
        if len(unique_ctypes) < len(components):
            raise AssertionError(
                f"Cannot create entity with components: {tuple(components)}."
                f"Adding multiple components of the same type to one"
                f"entity is not allowed."
            )

    id_ = world._entity_counter = world._entity_counter + 1
    bitmask = ZERO
    entdict = {}
    entcache = world._entity_cache
    for component in components:
        cc = component.__class__
        bitmask |= component._bitmask
        entdict[cc] = component
        entcache.setdefault(cc, set()).add(id_)
    world._entities[id_] = entdict
    world._entity_bitmasks[id_] = bitmask
    return id_


def add_component(
    entity_id: "EntityID",
    component: "Component",
    world: "World" = default_world,
) -> "None":
    """
    Add a single component instance to an entity.

    Will throw KeyError if the `Component` type was not registered using
    `register_component`, or if the entity doesn't exist in the given `World`.

    :param entity_id: ID of the entity to add the Component to.
    :param component: A single Component instances to add to the Entity.
    :param world: The World holding the entity.
    """
    entd = world._entities[entity_id]
    cc = component.__class__
    if __debug__:
        if cc in entd:
            raise AssertionError(
                f"Entity ID {entity_id} already has a {cc} component. Adding "
                f"multiple components of the same type to one entity is not "
                f"allowed."
            )
    entd[cc] = component
    world._entity_cache.setdefault(cc, set()).add(entity_id)
    world._entity_bitmasks[entity_id] |= component._bitmask


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
    entd = world._entities[entity_id]
    new_bitmask = ZERO
    entcache = world._entity_cache
    for c in components:
        cc = c.__class__
        if __debug__:
            if cc in entd:
                raise AssertionError(
                    f"Entity ID {entity_id} already has a {cc} component. "
                    f"Adding multiple components of the same type to one "
                    f"entity is not allowed."
                )
        new_bitmask |= c._bitmask
        # Waaay faster than entity.update({cc: c for ...}).
        entd[cc] = c
        entcache.setdefault(cc, set()).add(entity_id)
    world._entity_bitmasks[entity_id] = new_bitmask


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


def has_components(
    entity_id: "EntityID",
    component_types: "Iterable[Type[Component]]",
    world: "World" = default_world,
) -> "bool":
    """
    Check if a given entity has all of the specified `Component`s.

    Will throw a KeyError if the entity doesn't exist in this `World`.

    :param entity_id: ID of the entity to check
    :param component_types: Component type to check
    :param world: World to check for the entity
    :return: bool
    :raises KeyError: If the entity doesn't exist in this `World`.
    """
    d = world._entities[entity_id]
    return all(c in d for c in component_types)


def remove_component(
    entity_id: "EntityID",
    component_type: "Type[Component]",
    world: "World" = default_world,
) -> "None":
    """
    Remove the `Component` of a given type from an entity.

    Will throw a KeyError if the entity doesn't have a Component of the
    given type, or if the entity doesn't exist in this `World`.

    :param entity_id: ID of the entity to check
    :param component_type: Component type to check
    :param world: World to check for the entity
    :return: bool
    :raises KeyError: If the entity doesn't exist in this `World` or it
                      doesn't have the specified component.
    """
    del world._entities[entity_id][component_type]
    world._entity_cache[component_type].remove(entity_id)
    world._entity_bitmasks[entity_id] ^= component_type._bitmask


def delete_entity(
    entity_id: "EntityID", world: "World" = default_world
) -> "None":
    """
    Schedule an entity for deletion from the `World`. Thread-safe.

    The entity will be deleted on the next call to `process_pending_deletions`.

    :param entity_id: ID of the entity to schedule for deletion
    :param world: The World to delete the entity from
    """
    world._entities_to_delete.add(entity_id)


def delete_entity_immediately(
    entity_id: "EntityID", world: "World" = default_world
) -> "None":
    """
    Delete an entity from a given `World` immediately. *Not* thread-safe.

    Idempotent. Will *not* throw a KeyError if the entity doesn't exist in
    this `World`.

    :param entity_id: ID of the entity to delete
    :param world: The World to delete the entity from
    """
    ctypes = world._entities.pop(entity_id, ())
    for ct in ctypes:
        world._entity_cache[ct].discard(entity_id)
    world._entity_bitmasks.pop(entity_id, None)


def process_pending_deletions(world: "World") -> "None":
    """
    Process pending entity deletions.

    Equivalent to calling `delete_entity_immediately(entity_id)` on all
    entities for which `delete_entity(entity_id)` had been called for since
    the last call to `process_pending_deletions`.

    Idempotent. *Not* thread-safe.

    :param world: The World to delete the entities from
    """
    for entid in world._entities_to_delete:
        delete_entity_immediately(entid, world)


SERIALIZED_COMPONENTS_KEY = 0
SERIALIZED_ENTITIES_KEY = 1
_serialized_key_type = int


# This, sadly, has to have extremely loose typing until at least PyPy hits 3.8.
# TypedDict came to `typing` way too late.
# There's lots of type: ignore here, thanks to that.
def serialize_world(  # type: ignore
    world: "World",
) -> "Dict[_serialized_key_type, Any]":
    """
    Serialize a World and all the Entities and Components inside it.

    Returns a Python dictionary that can be passed to `deserialize_world` to
    reconstruct the serialized world.

    You can for example, dump the output of `serialize_world` to a file with
    `json.dump`, to use as an effortless savegame format.
    """
    if not _all_components_serializable:
        raise ValueError(
            "Cannot serialize a World if the components aren't serializable."
        )

    # A mapping of component type names to indices in `component_types`
    reverse_components = {}
    component_types: "List[str]" = []

    entities = {}
    for ent_id, components in world._entities.items():
        serialized: "Dict[int, Any]" = {}  # type: ignore
        for ctype, cmpnt in components.items():
            if ctype not in reverse_components:
                idx = reverse_components[ctype] = len(component_types)
                component_types.append(ctype.__name__)
            else:
                idx = reverse_components[ctype]
            serialized[idx] = cmpnt.serialize()  # type: ignore
        entities[ent_id] = serialized  # type: ignore

    return {  # type: ignore
        SERIALIZED_COMPONENTS_KEY: component_types,
        SERIALIZED_ENTITIES_KEY: entities,  # type: ignore
    }


def deserialize_world(  # type: ignore
    serialized: "Dict[_serialized_key_type, Any]",
) -> "World":
    """
    Deserialize a dictionary as output by `serialize_world` into a `World`.

    If any of the component types that were registered in the serialized World
    are not registered when you call `deserialize_world`, or any of them
    have been renamed, this will fail and raise a ValueError.

    :return: World
    """
    if not _all_components_serializable:
        raise ValueError(
            "Cannot deserialize a World if the components aren't "
            "deserializable."
        )

    world = World()
    serialized_names = cast(
        "List[str]", serialized[SERIALIZED_COMPONENTS_KEY]  # type: ignore
    )
    component_types: "List[Type[Component]]" = [
        _component_names[name] for name in serialized_names
    ]
    serialized_entities = cast(
        "Dict[EntityID, Dict[int, str]]",
        serialized[SERIALIZED_ENTITIES_KEY],  # type: ignore
    )
    for ent_id, components in serialized_entities.items():
        cmp_instances = [
            component_types[i].deserialize(serialized)
            for i, serialized in components.items()
        ]
        if ent_id > world._entity_counter:
            world._entity_counter = ent_id
        # This is pretty directly copied over from `add_component`
        bitmask = ZERO
        entdict = {}
        entcache = world._entity_cache
        for component in cmp_instances:
            cc = component.__class__
            bitmask |= component._bitmask
            entdict[cc] = component
            entcache.setdefault(cc, set()).add(ent_id)
        world._entities[ent_id] = entdict
        world._entity_bitmasks[ent_id] = bitmask

    return world
