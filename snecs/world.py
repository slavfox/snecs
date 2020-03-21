# Copyright (c) 2020 Slavfox
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""
Defines the World - the central object in snecs, which manages all the data.
"""
from typing import TYPE_CHECKING, cast

from snecs.component import Component

if TYPE_CHECKING:
    from typing import Type, Set, Dict, Optional
    from snecs._detail import Bitmask
    from snecs.typedefs import EntityID

__all__ = ["World", "default_world"]

DEFAULT_WORLD_NAME = "DEFAULT"

class World:
    """
    A container for all your entities, components and systems.

    Takes an optional ``name`` parameter that, if passed, will be used in the
    ``repr`` instead of the `id`.

    :param name: A human-readable name for this world, for debugging purposes.
                 The default world is called "default".
    :type name: str
    """

    _instances = {}

    __slots__ = (
        "_entity_counter",
        "_entities",
        "_entity_bitmasks",
        "_entity_cache",
        "_entities_to_delete",
        "name",
    )

    def __init__(self, name: "Optional[str]" = None) -> None:
        if name:
            if name in World._instances:
                raise ValueError(
                    f"A world with the name {name} already exists."
                )
            else:
                World._instances[name] = self

        self.name: "Optional[str]" = name
        self._entity_counter: "EntityID" = cast("EntityID", 0)
        self._entities: "Dict[EntityID, Dict[Type[Component], Component]]" = {}
        self._entity_bitmasks: "Dict[EntityID, Bitmask]" = {}
        self._entity_cache: "Dict[Type[Component], Set[EntityID]]" = {}
        self._entities_to_delete: "Set[EntityID]" = set()

    def __repr__(self) -> "str":
        """
        Return a pretty representation of the world, for debugging purposes.
        """
        if self.name is not None:
            return f"<{self.name} World>"
        else:
            return f"<World {id(self)} ({self._entity_counter} entities)>"

    @classmethod
    def get_by_name(cls, name: str = DEFAULT_WORLD_NAME):
        """
        Get a World instance by name.

        This is obviously slower than just passing the World around,

        :param name:
        :return:
        """
        return


#: The default World, used if you don't explicitly pass one.
default_world = World(DEFAULT_WORLD_NAME)
