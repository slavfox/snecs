# Copyright (c) 2020 Slavfox
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""
Functions for interacting with the ECS.

All the functions in this module are reexported under the ``snecs`` root for
convenience, so that you can::

    from snecs import new_entity

    new_entity(...)

    # or

    import snecs

    snecs.new_entity(...)
    snecs.add_component(...)

Instead of having to type ``snecs.ecs`` every time.
"""
from typing import TYPE_CHECKING
from typing import cast as _cast
from types import MappingProxyType as _MappingProxy

from snecs._detail import ZERO as _ZERO
from snecs.component import _component_names
from snecs.world import World as _World
from snecs.world import default_world as _default_world

if TYPE_CHECKING:
    from typing import (
        Type,
        Iterable,
        Collection,
        TypeVar,
        Mapping,
        Dict,
        Any,
        List,
        Optional,
    )
    from snecs.component import Component
    from snecs.typedefs import EntityID, SerializedWorldType

    C = TypeVar("C", bound=Component)

__all__ = [
    "add_component",
    "add_components",
    "all_components",
    "delete_entity_immediately",
    "deserialize_world",
    "entity_component",
    "entity_components",
    "exists",
    "has_component",
    "has_components",
    "new_entity",
    "process_pending_deletions",
    "remove_component",
    "schedule_for_deletion",
    "serialize_world",
    "SERIALIZED_COMPONENTS_KEY",
    "SERIALIZED_ENTITIES_KEY",
]


def new_entity(
    components: "Collection[Component]" = (), world: "_World" = _default_world
) -> "EntityID":
    """
    Create an entity in a World with the given Components, returning its ID.

    :param world: World to create the entity in.
    :type world: Optional[`World`]

    :param components: An iterable of Component instances to attach to the
                       entity.
    :type components: Collection[:class:`~snecs.Component`]

    :return: ID of the newly created entity.
    :rtype: `EntityID`
    """
    unique_ctypes = {c.__class__ for c in components}
    if len(unique_ctypes) < len(components):
        raise ValueError(
            f"Cannot create entity with components: {tuple(components)}. "
            f"Adding multiple components of the same type to one "
            f"entity is not allowed."
        )

    bitmask = _ZERO
    entdict = {}
    entcache = world._entity_cache
    id_ = world._entity_counter + 1
    for component in components:
        cc = component.__class__
        bitmask |= component._bitmask
        entdict[cc] = component
        entcache.setdefault(cc, set()).add(id_)

    world._entities[id_] = entdict
    world._entity_bitmasks[id_] = bitmask
    world._entity_counter = id_
    return id_


def add_component(
    entity_id: "EntityID",
    component: "Component",
    world: "_World" = _default_world,
) -> "None":
    """
    Add a single component instance to an entity.

    .. warning::

        Adding multiple components of the same type to a single entity is
        invalid.

    :param entity_id: ID of the entity to add the Component to.
    :type entity_id: `EntityID`

    :param component: A single Component instances to add to the Entity.
    :type component: `Component`

    :param world: The World holding the entity.
    :type world: Optional[`World`]

    :raises KeyError: If the Component type was not registered, or if the
                      entity doesn't exist in the given World.

    :raises ValueError: If the entity already has a Component of the same type
                        as the given one.
    """
    entd = world._entities[entity_id]
    cc = component.__class__
    if cc in entd:
        # Adding multiple components of the same time will break shit. Heavily.
        #
        # First of all, all the components of that type other than the
        # last-added one will be effectively inaccessible, because component
        # mappings and the query caches are keyed on component types.
        #
        # Worse than that, they will also be unremovable - since after
        # removing a component type from an entity, it's considered to not
        # longer have a component of that type.
        #
        # Instead of dealing with all that, we just explicitly disallow this.
        # This was an AssertionError previously, but I feel it's important
        # enough to be a proper runtime check.
        raise ValueError(
            f"Tried to add a {cc.__name__} component to entity {entity_id}, "
            f"but it already has a component of that type."
        )
    entd[cc] = component
    world._entity_cache.setdefault(cc, set()).add(entity_id)
    world._entity_bitmasks[entity_id] |= component._bitmask


def add_components(
    entity_id: "EntityID",
    components: "Collection[Component]",
    world: "_World" = _default_world,
) -> "None":
    """
    Add components to an entity.

    See notes in `add_component`.

    :param entity_id: ID of the entity to add the Components to.
    :type entity_id: `EntityID`

    :param components: An iterable of Component instances to add to the Entity.
    :type components: Collection[:class:`~snecs.Component`]

    :param world: The World holding the entity.
    :type world: Optional[`World`]

    :raises KeyError: If any of the Component types was not registered, or if
                      the entity doesn't exist in the given World.

    :raises ValueError: If the entity already has a Component of the same type
                        as one of the given ones.
    """
    entd = world._entities[entity_id]
    new_bitmask = _ZERO
    entcache = world._entity_cache
    unique_ctypes = {c.__class__ for c in components}
    if len(unique_ctypes) < len(components) or unique_ctypes & entd.keys():
        # This is an error, so doesn't have to be fast
        existing = [c.__class__.__name__ for c in entd.keys()]
        raise ValueError(
            f"Tried to add duplicate components for entity {entity_id}: "
            f"{components} (entity already has {existing})."
        )

    for c in components:
        cc = c.__class__
        new_bitmask |= c._bitmask
        # Waaay faster than entity.update({cc: c for ...}).
        entd[cc] = c
        entcache.setdefault(cc, set()).add(entity_id)
    world._entity_bitmasks[entity_id] = new_bitmask


def entity_component(
    entity_id: "EntityID",
    component_type: "Type[C]",
    world: "_World" = _default_world,
) -> "C":
    """
    Get the Component instance of a given type for a specific entity.

    :param entity_id: ID of the entity to get the Component from.
    :type entity_id: `EntityID`

    :param component_type: Type of the component to fetch.
    :type component_type: Type[:class:`~snecs.Component`]

    :param world: The World to look up the entity in.
    :type world: Optional[`World`]

    :return: The instance of ``component_type`` that's assigned to the entity.
    :rtype: Instance of ``component_type``

    :raises KeyError: If the entity doesn't exist in this `World` or if it
                      doesn't have the requested Component.
    """
    return world._entities[entity_id][component_type]  # type: ignore


def entity_components(
    entity_id: "EntityID",
    components: "Iterable[Type[Component]]",
    world: "_World" = _default_world,
) -> "Dict[Type[Component], Component]":
    """
    Get the given instances of given Component types for a specific entity.

    :param entity_id: ID of the entity to get the Components from.
    :type entity_id: `EntityID`

    :param components: An iterable of Component types to look up.
    :type components: Iterable[Type[:class:`~snecs.Component`]]

    :param world: The World to look up the entity in.
    :type world: Optional[`World`]

    :return: A dictionary mapping each given Component type to the instance of
             that type attached to the given entity. Note that mutations of
             this dictionary do not affect the world.
    :rtype: Dict[Type[Component], Component]

    :raises KeyError: If the entity doesn't exist in this `World` or if it
                      doesn't have any of the requested Components.
    """
    entd = world._entities[entity_id]
    return {cc: entd[cc] for cc in components}


def all_components(
    entity_id: "EntityID", world: "_World" = _default_world
) -> "Mapping[Type[Component], Component]":
    """
    Get a mapping of all Components for a specific entity in a given World.

    :param entity_id: ID of the entity to get the Component from.
    :type entity_id: `EntityID`

    :param world: The World to look up the entity in.
    :type world: Optional[`World`]

    :return: An immutable mapping between each Component type of which the
             entity has an instance, and the instance.
    :rtype: Mapping[Type[Component], Component]

    :raises KeyError: If the entity doesn't exist in this `World`.
    """
    return _MappingProxy(world._entities[entity_id])


def has_component(
    entity_id: "EntityID",
    component_type: "Type[Component]",
    world: "_World" = _default_world,
) -> "bool":
    """
    Check if a given entity has a specific Component.

    ::

        if not has_component(entity_id, FreezeStatus):
            do_stuff(entity_id)

    :param entity_id: ID of the entity to check
    :type entity_id: `EntityID`

    :param component_type: Component type to check for
    :type component_type: Type[:class:`~snecs.Component`]

    :param world: World to check for the entity
    :type world: Optional[`World`]

    :return: Whether the entity has a component of the given type.
    :rtype: bool

    :raises KeyError: If the entity doesn't exist in this `World`.
    """
    return component_type in world._entities[entity_id]


def has_components(
    entity_id: "EntityID",
    component_types: "Iterable[Type[Component]]",
    world: "_World" = _default_world,
) -> "bool":
    """
    Check if a given entity has all of the specified Components.

    :param entity_id: ID of the entity to check
    :type entity_id: `EntityID`

    :param component_types: Iterable of component types to check for
    :type component_types: Iterable[Type[:class:`~snecs.Component`]]

    :param world: World to check for the entity
    :type world: Optional[`World`]

    :return: Whether the entity has components of all of the given types.
    :rtype: bool

    :raises KeyError: If the entity doesn't exist in this `World`.
    """
    d = world._entities[entity_id]
    return all(c in d for c in component_types)


def remove_component(
    entity_id: "EntityID",
    component_type: "Type[Component]",
    world: "_World" = _default_world,
) -> "None":
    """
    Remove the component of a given type from an entity.

    :param entity_id: ID of the entity to remove the component from.
    :type entity_id: `EntityID`

    :param component_type: Type of the component to remove.
    :type component_type: Type[:class:`~snecs.Component`]

    :param world: The World to look up the entity in.
    :type world: Optional[`World`]

    :raises KeyError: If the entity doesn't exist in this `World` or it
                      doesn't have the specified component.
    """
    del world._entities[entity_id][component_type]
    world._entity_cache[component_type].remove(entity_id)
    world._entity_bitmasks[entity_id] ^= component_type._bitmask


def schedule_for_deletion(
    entity_id: "EntityID", world: "_World" = _default_world
) -> "None":
    """
    Schedule an entity for deletion from the World. Thread-safe.

    The entity will be deleted on the next call to `process_pending_deletions`.

    This method is idempotent - you can schedule an entity for deletion many
    times, and it will only be deleted once.

    .. warning::

        This will **not** raise an error if the entity doesn't exist.
        However, calling this with an entity ID that isn't in the World
        will put the World into an unrecoverable state - all later calls to
        `process_pending_deletions` will fail.

        To prevent this from happening, make sure you're calling
        `process_pending_deletions` only *after* all your Systems have
        finished running for this frame, so that they won't have a reference
        to the dead entity on the next loop.

        Calling `delete_entity_immediately` on an entity that is scheduled
        for deletion but hasn't been deleted yet is safe, and will remove the
        entity from the deletion queue.

        If there is a risk of an entity you want to delete being already
        gone, do this instead::

            from snecs.ecs import exists, schedule_for_deletion

            if exists(entity_id, world):
                schedule_for_deletion(entity_id, world)


    :param entity_id: ID of the entity to schedule for deletion
    :type entity_id: `EntityID`

    :param world: The World to delete the entity from
    :type world: Optional[`World`]
    """
    world._entities_to_delete.add(entity_id)


def exists(entity_id: "EntityID", world: "_World") -> "bool":
    """
    Check whether an entity exists in this World.

    This is a convenience function that should not be necessary except in
    concurrent code or with uncertain usage of `schedule_for_deletion` (see
    the documentation of that function).

    :param entity_id: ID of the entity to check for
    :type entity_id: `EntityID`

    :param world: The World to check for the existence of the entity
    :type world: `World`

    :return: True if the entity exists in the World, False otherwise
    :rtype: bool
    """
    return entity_id in world._entities


def delete_entity_immediately(
    entity_id: "EntityID", world: "_World" = _default_world
) -> "None":
    """
    Delete an entity from a given `World` immediately. *Not* thread-safe.

    Idempotent. Will *not* throw a KeyError if the entity doesn't exist in
    this `World`.

    :param entity_id: ID of the entity to delete
    :type entity_id: `EntityID`

    :param world: The World to delete the entity from
    :type world: Optional[`World`]
    """
    ctypes = world._entities.pop(entity_id, ())
    for ct in ctypes:
        world._entity_cache[ct].discard(entity_id)
    world._entity_bitmasks.pop(entity_id, None)
    world._entities_to_delete.discard(entity_id)


def process_pending_deletions(world: "_World" = _default_world) -> "None":
    """
    Process pending entity deletions.

    Equivalent to calling `delete_entity_immediately` on all
    entities for which `schedule_for_deletion` had been called for since
    the last call to ``process_pending_deletions``.

    Idempotent. *Not* thread-safe.

    :param world: The World to delete the entities from
    :type world: Optional[`World`]
    """
    # Make a copy so that we can safely iterate over it
    for entid in list(world._entities_to_delete):
        delete_entity_immediately(entid, world)


#: See `serialize_world`
SERIALIZED_COMPONENTS_KEY = 0
#: See `serialize_world`
SERIALIZED_ENTITIES_KEY = 1


# This, sadly, has to have extremely loose typing until at least PyPy hits 3.8.
# TypedDict came to `typing` way too late.
# There's lots of type: ignore here, thanks to that.
def serialize_world(world: "_World" = _default_world) -> "SerializedWorldType":
    """
    Serialize a World and all the Entities and Components inside it.

    **All Component classes in your World must be serializable for this to
    run.**

    Returns a Python dictionary that can be passed to `deserialize_world` to
    reconstruct the serialized world.

    You can for example, dump the output of `serialize_world` to a file with
    `json.dump`, to use as an effortless savegame format::

        import json

        def save_to_file(world: World, filename: str):
            with open(filename, "w") as f:
                json.dump(serialize_world(world), f)

    The resulting dict looks like this::

        serialized = {
            SERIALIZED_COMPONENTS_KEY: ["ComponentType1",...],
            SERIALIZED_ENTITIES_KEY: {
                entity_id: {
                    component_idx: serialized_component_data,
                    ...
                },
                entity_id: ...,
                ...
            }
        }

    Where:

    - ``serialized[SERIALIZED_COMPONENTS_KEY]`` is a list of names of the
      Component classes present in the World.
    - ``serialized[SERIALIZED_ENTITIES_KEY]`` is a dictionary mapping entity
      IDs to dictionaries representing their components.

      - Each of the dictionaries in ``serialized[SERIALIZED_ENTITIES_KEY]``
        maps indices of component types in
        ``serialized[SERIALIZED_COMPONENTS_KEY]`` to that component's
        serialized data.

        For example, if ``serialized[SERIALIZED_COMPONENTS_KEY]`` is
        ``[A, B, C]``, the index ``1`` would indicate that the value is a
        serialized instance of a ``B`` component.

    :param world: The World to serialize.
    :type world: Optional[`World`]

    :return: A serialized dictionary representing this World, which can be
             deserialized with `deserialize_world`.
    :rtype: `SerializedWorldType`

    :raise AttributeError: If any component in the World is not serializable.
    """
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


def deserialize_world(
    serialized: "SerializedWorldType", name: "Optional[str]" = None
) -> "_World":
    """
    Deserialize the output of `serialize_world` into a new `World`.

    If any of the component types that were registered in the serialized World
    are not registered when you call `deserialize_world`, or any of them
    have been renamed, this will fail and raise a ValueError.

    :param serialized: A serialized world, as output by `serialize_world`.
    :type serialized: `SerializedWorldType`

    :param name: An optional name to use for the new World. See `World`.
    :type name: Optional[str]

    :return: A new World with the data from the serialized one.
    :rtype: `World`
    """
    world = _World(name=name)
    serialized_names = _cast(
        "List[str]", serialized[SERIALIZED_COMPONENTS_KEY]
    )
    component_types: "List[Type[Component]]" = [
        _component_names[name] for name in serialized_names
    ]
    serialized_entities = _cast(
        "Dict[EntityID, Dict[int, str]]", serialized[SERIALIZED_ENTITIES_KEY]
    )
    for ent_id, components in serialized_entities.items():
        cmp_instances = [
            component_types[i].deserialize(serialized)
            for i, serialized in components.items()
        ]
        if ent_id > world._entity_counter:
            world._entity_counter = ent_id
        # This is pretty directly copied over from `add_component`
        bitmask = _ZERO
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
