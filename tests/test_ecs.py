# Copyright (c) 2020 Slavfox
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from snecs.component import RegisteredComponent
from snecs.ecs import (
    add_component,
    add_components,
    delete_entity_immediately,
    entity_component,
    entity_components,
    has_component,
    has_components,
    new_entity,
    process_pending_deletions,
    remove_component,
    schedule_for_deletion,
)
from snecs.types import EntityID
from snecs.world import World


class TestComponent(RegisteredComponent):
    pass


def test_entity_creation_no_components():
    world = World()
    for i in range(3):
        ent_id = new_entity(world=world)
        assert ent_id == EntityID(i + 1)  # entity IDs start at 1
    world2 = World()
    for i in range(3):
        ent_id = new_entity(world=world2)
        assert ent_id == EntityID(i + 1)


def test_entity_creation_adds_to_entity_cache():
    world = World()
    c = TestComponent()
    ent_id = new_entity((c,), world=world)
    assert ent_id in world._entities
    assert world._entities[ent_id] == {TestComponent: c}

    assert ent_id in world._entity_bitmasks
    assert world._entity_bitmasks[ent_id] == TestComponent._bitmask

    assert TestComponent in world._entity_cache
    assert world._entity_cache[TestComponent] == {ent_id}
