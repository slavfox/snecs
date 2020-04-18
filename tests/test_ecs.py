# Copyright (c) 2020 Slavfox
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import json
from copy import copy, deepcopy

import pytest
import snecs.ecs
from snecs.ecs import (
    SERIALIZED_COMPONENTS_KEY,
    SERIALIZED_ENTITIES_KEY,
    add_component,
    add_components,
    all_components,
    delete_entity_immediately,
    deserialize_world,
    entity_component,
    entity_components,
    exists,
    has_component,
    has_components,
    move_world,
    new_entity,
    process_pending_deletions,
    remove_component,
    schedule_for_deletion,
    serialize_world,
)
from snecs.typedefs import EntityID
from snecs.world import World, default_world


def test_dunder_all(missing_dunder_all_names):
    assert not missing_dunder_all_names(snecs.ecs)


def test_entity_creation_no_components():
    world = World()
    for i in range(3):
        ent_id = new_entity(world=world)
        assert ent_id == EntityID(i + 1)  # entity IDs start at 1
    world = World()
    for i in range(3):
        ent_id = new_entity(world=world)
        assert ent_id == EntityID(i + 1)


def test_entity_creation_adds_to_entity_cache(world, component_a):
    c = component_a()
    ent_id = new_entity((c,), world=world)
    assert ent_id in world._entities
    assert world._entities[ent_id] == {component_a: c}

    assert ent_id in world._entity_bitmasks
    assert world._entity_bitmasks[ent_id] == component_a._bitmask

    assert component_a in world._entity_cache
    assert world._entity_cache[component_a] == {ent_id}


def test_entity_creation_disallows_duplicate_components(world, component_a):
    pre_counter = copy(world._entity_counter)
    pre_entcache = deepcopy(world._entity_cache)
    pre_entities = deepcopy(world._entities)
    pre_bitmasks = deepcopy(world._entity_bitmasks)
    with pytest.raises(
        ValueError,
        match=r".*Adding multiple components of the same type to one entity "
        r"is not allowed.*",
    ):
        new_entity((component_a(), component_a()), world=world)
    # Make sure the world state hasn't changed
    assert world._entity_counter == pre_counter
    assert world._entities == pre_entities
    assert world._entity_cache == pre_entcache
    assert world._entity_bitmasks == pre_bitmasks


def test_add_component(world, empty_entity, component_a):
    assert empty_entity not in world._entity_cache.get(component_a, {})
    assert not world._entity_bitmasks[empty_entity] & component_a._bitmask
    assert component_a not in world._entities[empty_entity]
    c = component_a()
    add_component(empty_entity, c, world=world)
    assert world._entities[empty_entity][component_a] == c
    assert empty_entity in world._entity_cache[component_a]
    assert world._entity_bitmasks[empty_entity] & component_a._bitmask


def test_add_component_no_entity(world, component_a):
    with pytest.raises(KeyError):
        add_components(23, component_a(), world=world)


def test_add_duplicate_component_error(world, empty_entity, component_a):
    c = component_a()
    add_component(empty_entity, c, world=world)
    with pytest.raises(
        ValueError,
        match=f"{component_a.__name__}.*already has a component of that type",
    ):
        add_component(empty_entity, c, world=world)
    assert world._entities[empty_entity][component_a] == c
    assert empty_entity in world._entity_cache[component_a]
    assert world._entity_bitmasks[empty_entity] & component_a._bitmask


def test_add_components(world, empty_entity, component_a, component_b):
    assert empty_entity not in world._entity_cache.get(component_a, {})
    assert component_a not in world._entities[empty_entity]
    assert empty_entity not in world._entity_cache.get(component_b, {})
    assert component_b not in world._entities[empty_entity]
    assert not world._entity_bitmasks[empty_entity] & (
        component_a._bitmask | component_b._bitmask
    )
    ca = component_a()
    cb = component_b()
    add_components(empty_entity, (ca, cb), world=world)
    assert world._entities[empty_entity][component_a] == ca
    assert empty_entity in world._entity_cache[component_a]
    assert world._entities[empty_entity][component_b] == cb
    assert empty_entity in world._entity_cache[component_b]
    assert world._entity_bitmasks[empty_entity] & (
        component_a._bitmask | component_b._bitmask
    )


def test_add_components_no_entity(world, component_a):
    with pytest.raises(KeyError):
        add_components(23, (component_a(),), world=world)


def test_add_existing_component_error(
    world, empty_entity, component_a, component_b
):
    c = component_a()
    add_component(empty_entity, c, world=world)
    ca = component_a()
    cb = component_b()
    with pytest.raises(
        ValueError, match=f"duplicate components.*{component_a.__name__}",
    ):
        add_components(empty_entity, (ca, cb), world=world)
    assert world._entities[empty_entity][component_a] == c
    assert empty_entity in world._entity_cache[component_a]
    assert component_b not in world._entities[empty_entity]
    assert empty_entity not in world._entity_cache.get(component_b, {})
    assert not world._entity_bitmasks[empty_entity] & component_b._bitmask


def test_add_duplicate_components_error(world, empty_entity, component_a):
    c1 = component_a()
    c2 = component_a()
    with pytest.raises(
        ValueError, match=f"duplicate components.*{component_a.__name__}",
    ):
        add_components(empty_entity, (c1, c2), world=world)
    assert world._entities[empty_entity] == {}
    assert empty_entity not in set().union(*world._entity_cache.values())


def test_entity_component_has(world, empty_entity, component_a):
    c = component_a()
    add_component(empty_entity, c, world=world)
    assert entity_component(empty_entity, component_a, world=world) == c


def test_entity_component_not_has(
    world, empty_entity, component_a, component_b
):
    c = component_a()
    add_component(empty_entity, c, world=world)
    with pytest.raises(KeyError):
        entity_component(empty_entity, component_b, world=world)


def test_entity_component_no_entity(world, component_a):
    with pytest.raises(KeyError):
        entity_components(23, component_a, world=world)


def test_entity_components_has_all(
    world, empty_entity, component_a, component_b
):
    ca = component_a()
    cb = component_b()
    add_components(empty_entity, (ca, cb), world=world)
    assert entity_components(
        empty_entity, (component_a, component_b), world=world
    ) == {component_a: ca, component_b: cb}


def test_entity_components_not_has(
    world, entity_with_cmp_a, component_a, component_b
):
    with pytest.raises(KeyError):
        entity_components(
            entity_with_cmp_a, (component_b, component_b), world=world
        )


def test_entity_components_no_entity(world, component_a):
    with pytest.raises(KeyError):
        entity_components(23, (component_a,), world=world)


def test_all_components_empty(world, empty_entity):
    assert all_components(empty_entity, world=world) == {}


def test_has_component_true(entity_with_cmp_a, component_a, world):
    assert has_component(entity_with_cmp_a, component_a, world)


def test_has_component_false(empty_entity, world, component_a):
    assert not has_component(empty_entity, component_a, world)


def test_has_components_all(empty_entity, world, component_a, component_b):
    add_components(empty_entity, (component_a(), component_b()), world)
    assert has_components(empty_entity, (component_a, component_b), world)


def test_has_components_not_all(
    entity_with_cmp_a, world, component_a, component_b
):
    assert not has_components(
        entity_with_cmp_a, (component_a, component_b), world
    )


def test_has_components_none(empty_entity, world, component_a, component_b):
    assert not has_components(empty_entity, (component_a, component_b), world)


def test_has_components_no_arg(entity_with_cmp_a, world):
    assert has_components(entity_with_cmp_a, (), world)


def test_remove_component_has(entity_with_cmp_a, world, component_a):
    assert entity_with_cmp_a in world._entity_cache[component_a]
    assert component_a in world._entities[entity_with_cmp_a]
    assert world._entity_bitmasks[entity_with_cmp_a] & component_a._bitmask
    remove_component(entity_with_cmp_a, component_a, world)
    assert entity_with_cmp_a not in world._entity_cache[component_a]
    assert component_a not in world._entities[entity_with_cmp_a]
    assert not world._entity_bitmasks[entity_with_cmp_a] & component_a._bitmask


def test_remove_component_not_has(empty_entity, world, component_a):
    with pytest.raises(KeyError):
        remove_component(empty_entity, component_a, world)


def test_schedule_for_deletion(empty_entity, world):
    schedule_for_deletion(empty_entity, world)
    assert empty_entity in world._entities_to_delete


@pytest.mark.xfail
def test_schedule_for_deletion_wrong_entity(world):
    # this is a programming error, safe_schedule_for_deletion exists
    with pytest.raises(KeyError):
        schedule_for_deletion(23, world)


def test_postponed_deletion(entity_with_cmp_a, world, component_a):
    schedule_for_deletion(entity_with_cmp_a, world)
    process_pending_deletions(world)
    assert entity_with_cmp_a not in world._entities
    assert entity_with_cmp_a not in world._entity_cache[component_a]
    assert entity_with_cmp_a not in world._entity_bitmasks


def test_exists(world):
    ent = new_entity((), world)
    assert exists(ent, world)
    assert not exists(ent + 1, world)


def test_serialize(world, serializable_component_a, serializable_component_b):
    ent1 = new_entity(
        (serializable_component_a(1), serializable_component_b(2, 3)), world
    )

    ent2 = new_entity(
        (
            serializable_component_a("abc"),
            serializable_component_b([1, 2], [3, 4]),
        ),
        world,
    )

    serialized = serialize_world(world)
    assert serialized == {
        SERIALIZED_COMPONENTS_KEY: [
            serializable_component_a.__name__,
            serializable_component_b.__name__,
        ],
        SERIALIZED_ENTITIES_KEY: {
            ent1: {0: 1, 1: (2, 3)},
            ent2: {0: "abc", 1: ([1, 2], [3, 4])},
        },
    }

    new_world = deserialize_world(json.loads(json.dumps(serialized)))
    new_serialized = serialize_world(new_world)
    assert serialized == new_serialized

    empty_world = move_world(new_world, World())
    assert serialize_world(empty_world) == new_serialized
