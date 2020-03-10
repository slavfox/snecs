# Copyright (c) 2020 Slavfox
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""
Base Component classes and the functions necessary to make them work.
"""
from typing import TYPE_CHECKING, TypeVar
from abc import ABCMeta

from snecs._detail import Bitmask, InvariantDict
from snecs.filters import AndExpr, Expr, NotExpr, OrExpr, Term

if TYPE_CHECKING:
    from typing import Type

__all__ = ["Component", "register_component"]


class ComponentMeta(ABCMeta):
    """
    Metaclass for Components, supporting filter expression syntax.

    This exists because the magic methods have to be defined on the metaclass,
    which Component classes are instances of; just like defining ``__add__``
    on a class ``Foo`` lets you do::

        foo = Foo()
        foo + 1  # calls ``foo.__add__(1)``
        Foo + 1  # TypeError: ...

    Defining bitwise operations on the metaclass lets you apply them to
    *classes* with that metaclass::

        FooComponent & BarComponent  # calls ComponentMeta.__and__
        foo = FooComponent()
        bar = BarComponent()
        foo & bar  # TypeError: ...
    """

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
    """
    Base Component class.

    snecs components *must* subclass `Component`, and be registered with
    `register_component` if they are going to be instantiated::

        @register_component
        class MyComponent(Component):
            ...

    If running in debug mode (without the `-O` flag), snecs will warn
    about using unregistered components or ones that don't inherit from
    `Component`.
    """

    _bitmask: "Bitmask"
    __slots__ = ()


CType = TypeVar("CType", bound=Component)


class _ComponentRegistry(InvariantDict["Type[Component]", "Bitmask"]):
    __slots__ = ()

    def value_for(self, key: "Type[Component]") -> "Bitmask":
        return Bitmask(1 << len(self))


_component_registry: "_ComponentRegistry" = _ComponentRegistry()


def register_component(component: "Type[CType]") -> "Type[CType]":
    """
    A decorator to register a class for use as a snecs component.

    Every class intended to be instantiated and used as a snecs component
    *must* inherit from `Component` and be registered by decorating it with
    ``@register_component``.
    """
    bitmask = _component_registry.add(component)
    component._bitmask = bitmask
    return component
