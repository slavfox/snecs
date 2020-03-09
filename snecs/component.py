# Copyright (c) 2020 Slavfox
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from typing import TYPE_CHECKING, TypeVar
from abc import ABCMeta

from snecs._detail import Bitmask, InvariantDict
from snecs.filters import AndExpr, Expr, NotExpr, OrExpr, Term

if TYPE_CHECKING:
    from typing import Type

__all__ = ["Component", "register_component"]


class ComponentMeta(ABCMeta):
    _bitmask: "Bitmask"

    def __and__(self, other: "Term") -> "AndExpr":
        if isinstance(other, Expr):
            return other & self
        return AndExpr(other, self)

    def __or__(self, other: "Term") -> "OrExpr":
        if isinstance(other, Expr):
            return other | self
        return OrExpr(other, self)

    def __invert__(self) -> "NotExpr":
        return NotExpr(self)


class Component(metaclass=ComponentMeta):
    _bitmask: "Bitmask"
    __slots__ = ()


CType = TypeVar("CType", bound=Component)


class _ComponentRegistry(InvariantDict["Type[Component]", "Bitmask"]):
    __slots__ = ()

    def value_for(self, key: "Type[Component]") -> "Bitmask":
        return Bitmask(1 << len(self))


_component_registry: "_ComponentRegistry" = _ComponentRegistry()


def register_component(component: "Type[CType]") -> "Type[CType]":
    bitmask = _component_registry.add(component)
    component._bitmask = bitmask
    return component
