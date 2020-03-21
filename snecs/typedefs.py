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

        def __add__(self, other: "int") -> "EntityID":  # noqa D105
            ...

        def __iadd__(self, other: "int") -> "EntityID":  # noqa D105
            ...


else:
    #: Effectively an integer `typing.NewType` that only allows incrementation.
    EntityID = int


__all__ = [
    "FilterExpressionType",
    "QueryType",
    "CompiledQueryType",
    "EntityID",
    "SerializedWorldType",
]

SerializedWorldType = Dict[int, Any]  # type: ignore
