# Copyright (c) 2020 Slavfox
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""
Type aliases to facilitate easier typing of snecs-dependent code.
"""
from typing import TYPE_CHECKING, Any, Dict

from snecs._filters import Expr as FilterExpressionType
from snecs.query import BaseQuery as QueryType
from snecs.query import CompiledQuery as CompiledQueryType

if TYPE_CHECKING:

    class EntityID(int):
        """
        A ``NewType(int)`` that only allows incrementation.
        """

        __slots__ = ()

        if TYPE_CHECKING:

            def __add__(self, other: "int") -> "EntityID":
                ...

            def __iadd__(self, other: "int") -> "EntityID":
                ...


else:
    EntityID = int


__all__ = [
    "FilterExpressionType",
    "QueryType",
    "CompiledQueryType",
    "EntityID",
    "SerializedWorldType",
]

SerializedWorldType = Dict[int, Any]  # type: ignore
