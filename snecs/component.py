# Copyright (c) 2020 Slavfox
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""
Base Component classes and the functions necessary to make them work.
"""
from typing import TYPE_CHECKING, TypeVar
from abc import ABC, ABCMeta

from snecs._detail import Bitmask, InvariantDict
from snecs.filters import AndExpr, Expr, NotExpr, OrExpr

if TYPE_CHECKING:
    from typing import Type, Any
    from snecs.filters import Term

    CType = TypeVar("CType", bound="Component")

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

    def __and__(self, other: "Term") -> "Term":
        if other is self:
            return self
        elif isinstance(other, Expr):
            return other.__rand__(self)
        return AndExpr(self, other)

    def __or__(self, other: "Term") -> "Term":
        if other is self:
            return self
        elif isinstance(other, Expr):
            return other.__ror__(self)
        return OrExpr(self, other)

    def __invert__(self) -> "NotExpr":
        return NotExpr(self)


class Component(ABC, metaclass=ComponentMeta):
    """
    Base Component class.

    snecs components *must* subclass `Component`, and be registered with
    `register_component` if they are going to be instantiated::

        @register_component
        class MyComponent(Component):
            ...

    Base and abstract Component classes don't have to be registered, as long as
    you're not going to instantiate them.

    If you want to use the snecs full-world serialization and make your
    typing extra tight, you should override `serialize` and `deserialize` in
    all your registered Components::

        @register_component
        class IntPairComponent(Component):
            ...
            def serialize(self):
                return (self.first, self.second)

            @classmethod
            def deserialize(cls, serialized):
                return cls(*serialized)
    """

    _bitmask: "Bitmask"
    __slots__ = ()

    def serialize(self) -> "Any":  # type: ignore
        """
        Serialize an instance of this component into a simpler type.

        Override this in all your Component classes to make use of snecs'
        full-World serialization feature.
        """
        raise NotImplementedError

    @classmethod
    def deserialize(  # type: ignore
        cls: "Type[CType]", serialized: "Any"
    ) -> "CType":
        """
        Deserialize a serialized instance of this component.

        Gets the output of `serialize` as an argument.

        Override this in all your Component classes to make use of snecs'
        full-World serialization feature.
        """
        raise NotImplementedError


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
