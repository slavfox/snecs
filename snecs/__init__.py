# Copyright (c) 2020 Slavfox
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""
snecs - a straightforward, nimble ECS for Python.

snecs is a pure Python 3.6+, dependency-free ECS library, heavily inspired by
Rust’s Legion, and aiming to be as fast and easy-to-use as possible.
"""
from snecs.component import Component, RegisteredComponent, register_component
from snecs.ecs import (
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
    new_entity,
    process_pending_deletions,
    remove_component,
    schedule_for_deletion,
    serialize_world,
)
from snecs.query import Query
from snecs.world import World

__all__ = [
    "World",
    "Component",
    "RegisteredComponent",
    "register_component",
    # Functions to interact with the actual ECS
    "new_entity",
    "add_component",
    "add_components",
    "entity_component",
    "entity_components",
    "has_component",
    "has_components",
    "all_components",
    "remove_component",
    "schedule_for_deletion",
    "delete_entity_immediately",
    "process_pending_deletions",
    "serialize_world",
    "deserialize_world",
    "exists",
    "Query",
]

__version_info__ = ("1", "0", "0")
__version__ = ".".join(__version_info__)
