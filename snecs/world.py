# Copyright (c) 2020 Slavfox
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from typing import TYPE_CHECKING, Dict

from snecs._detail import ZERO, EntityID
from snecs.component import Component, _component_registry

if TYPE_CHECKING:
    from typing import Type
    from snecs._detail import Bitmask

__all__ = ["World", "EntityID"]


class World:
    def __init__(self) -> None:
        self._entity_counter: "EntityID" = EntityID(0)
        self._entities: "Dict[EntityID, Dict[Type[Component], Component]]" = {}
        self._entity_bitmasks: "Dict[EntityID, Bitmask]" = {}

    def create_entity(self, *components: "Component") -> "EntityID":
        id_ = self._entity_counter = self._entity_counter + 1
        bitmask = ZERO
        entdict = {}
        for component in components:
            bitmask |= _component_registry[component.__class__]
            entdict[component.__class__] = component
        self._entities[id_] = entdict
        self._entity_bitmasks[id_] = bitmask
        return id_
