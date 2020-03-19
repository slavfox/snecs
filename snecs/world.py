# Copyright (c) 2020 Slavfox
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""
snecs World - the repository of all the data in your game.
"""
from typing import TYPE_CHECKING, Dict

from snecs._detail import EntityID
from snecs.component import Component

if TYPE_CHECKING:
    from typing import Type, Set
    from snecs._detail import Bitmask

__all__ = ["World", "EntityID"]


class World:
    """
    A container for all your entities, components and systems.
    """

    __slots__ = (
        "_entity_counter",
        "_entities",
        "_entity_bitmasks",
        "_entity_cache",
        "_entities_to_delete",
    )

    def __init__(self) -> None:
        self._entity_counter: "EntityID" = EntityID(0)
        self._entities: "Dict[EntityID, Dict[Type[Component], Component]]" = {}
        self._entity_bitmasks: "Dict[EntityID, Bitmask]" = {}
        self._entity_cache: "Dict[Type[Component], Set[EntityID]]" = {}
        self._entities_to_delete: "Set[EntityID]" = set()


default_world = World()
