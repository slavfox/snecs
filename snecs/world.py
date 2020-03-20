# Copyright (c) 2020 Slavfox
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""
snecs World - the repository of all the data in your game.
"""
from typing import TYPE_CHECKING, cast

from snecs.component import Component

if TYPE_CHECKING:
    from typing import Type, Set, Dict, Optional
    from snecs._detail import Bitmask
    from snecs.types import EntityID

__all__ = ["World"]


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
        "name",
    )

    def __init__(self, name: "Optional[str]" = None) -> None:
        self.name: "Optional[str]" = name
        self._entity_counter: "EntityID" = cast("EntityID", 0)
        self._entities: "Dict[EntityID, Dict[Type[Component], Component]]" = {}
        self._entity_bitmasks: "Dict[EntityID, Bitmask]" = {}
        self._entity_cache: "Dict[Type[Component], Set[EntityID]]" = {}
        self._entities_to_delete: "Set[EntityID]" = set()

    def __repr__(self) -> "str":
        if self.name is not None:
            return f"<{self.name} World>"
        else:
            return f"<World ({self._entity_counter} entities)>"


default_world = World("default")
