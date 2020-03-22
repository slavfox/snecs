# Copyright (c) 2020 Slavfox
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""
Base Component classes and the functions necessary to make them work.
"""
from typing import TYPE_CHECKING
from abc import ABC, ABCMeta

from snecs._detail import Bitmask, InvariantDict
from snecs._filters import AndExpr, Expr, NotExpr, OrExpr

if TYPE_CHECKING:
    from typing import Type, Any, Dict, TypeVar
    from snecs._filters import Term

    CType = TypeVar("CType", bound="Component")

__all__ = ["Component", "RegisteredComponent", "register_component"]


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

    Other than that, there are no restrictions on what Components should be.
    They can be anything as simple as an integer::

        @register_component
        class IntComponent(int, Component):
            pass

    Or as complex as you want::

        @register_component
        class BigComponent(Component):
            __slots__ = ('a', 'b', 'c', 'd', ...)

            def __init__(a, b, c, d, ...):
                ...

            def __str__(self):
                ...

            ...

    If you want to use the snecs full-world serialization, you should
    override `serialize` and `deserialize` in *all* your registered
    Components::

        @register_component
        class IntPairComponent(Component):
            ...
            def serialize(self):
                return (self.first, self.second)

            @classmethod
            def deserialize(cls, serialized):
                return cls(*serialized)

    You *must* define either both, or neither of those two methods.
    Registering a class that only defines one of those is an error.

    If you register a class that defines `serialize` or
    `deserialize`, *all* of your registered classes must define them.
    Likewise, if you register a class that doesn't define `serialize` and
    `deserialize`, *none* of your registered classes can define them.
    """

    _bitmask: "Bitmask"
    __slots__ = ()

    def serialize(self) -> "Any":  # type: ignore
        """
        Serialize an instance of this component into a simpler type.

        Override this in all your Component classes to make use of snecs'
        full-World serialization feature.
        """
        raise AttributeError(
            f"{self.__class__} doesn't define serialize()"
            f"and so is not serializable."
        )

    @classmethod
    def deserialize(  # type: ignore
        cls: "Type[CType]", serialized: "Any"
    ) -> "CType":
        """
        Deserialize a serialized instance of this component.

        Will get the output of `serialize` as an argument.

        Override this in all your Component classes to make use of snecs'
        full-World serialization feature.
        """
        raise AttributeError(
            f"{cls} doesn't define deserialize()"
            f"and so is not deserializable."
        )


class _ComponentRegistry(InvariantDict["Type[Component]", "Bitmask"]):
    __slots__ = ()

    def value_for(self, key: "Type[Component]") -> "Bitmask":
        return Bitmask(1 << len(self))


_component_registry: "_ComponentRegistry" = _ComponentRegistry()
_component_names: "Dict[str, Type[Component]]" = {}


def _overrides_serialize(cls: "Type[Component]") -> "bool":
    return cls.serialize is not Component.serialize  # type: ignore


def _overrides_deserialize(cls: "Type[Component]") -> "bool":
    # This is a bit of jank, so it deserves an explanation.
    #
    # serialize() is a normal method, so we can just test if it's the base
    # one directly. On the other hand, deserialize() is a class method - so
    # trying to access cls.deserialize goes through the classmethod
    # descriptor and returns a method bound to `cls`. This means it
    # will never be Component.deserialize. Uh oh!
    #
    # Luckily, we have another trick up our sleeve. Through that same
    # mechanism, B.deserialize is a bound *method*, and not a function (as
    # unbound methods are).
    #
    # You might remember that bound methods hold a reference to the
    # underlying function object in their .__func__ attribute. So, to check
    # if the class passed as an argument overrides `deserialize`, we first
    # check:
    if (
        getattr(cls.deserialize, "__func__", None)  # type: ignore
        is Component.deserialize.__func__  # type: ignore
    ):
        # and if so,
        return False
    # Otherwise, if we landed here, we know that `deserialize` is not a
    # classmethod, *or* it's a classmethod different from Component.serialize.
    # Either way, it's not the base implementation, so we happily
    return True


def register_component(component: "Type[CType]") -> "Type[CType]":
    """
    A decorator to register a class for use as a snecs component.

    Every class intended to be instantiated and used as a snecs component
    *must* inherit from `Component` and be registered by decorating it with
    ``@register_component``.
    """
    # we're going to be using this a lot
    cn = component.__name__
    if component in _component_registry:
        raise ValueError(
            f"Component class {cn} is already registered. Cannot register "
            f"the same component class twice. (did you accidentally "
            f"@register_component a RegisteredComponent subclass?)"
        )
    has_deserialize = _overrides_deserialize(component)
    has_serialize = _overrides_serialize(component)

    serializable = False

    if has_serialize:
        if not has_deserialize:
            raise TypeError(
                f"Component class {cn} has an overriden `serialize()` but "
                f"does not override `deserialize()`. You must implement "
                f"either both or neither of those methods in registered "
                f"component classes."
            )
        serializable = True
    elif has_deserialize:
        raise TypeError(
            f"Component class {cn} has an overriden `deserialize()` but does "
            f"not override `serialize()`. You must implement either both or "
            f"neither of those methods in registered component classes."
        )
    if cn in _component_names and serializable:
        raise ValueError(
            f"A Component class named {cn} is already registered. Cannot "
            f"register a serializable Component class with a non-unique name."
        )
    bitmask = _component_registry.add(component)
    _component_names[cn] = component
    component._bitmask = bitmask
    return component


class RegisteredComponent(Component):
    """
    A convenience `Component` subclass for auto-registering components.

    The following two ways of defining a component are equivalent::

        @register_component
        class MyComponent1(snecs.Component):
            ...

        class MyComponent2(snecs.RegisteredComponent):
            ...

    Bear in mind, however, that all subclasses of a RegisteredComponent
    subclass will also get registered. Registering unnecessary components
    does have a slight performance and memory impact, so it's better to
    explicitly use `register_component`, or use ``RegisteredComponent`` as a
    mixin on leaf classes only::

        class AbstractComponent(snecs.Component, ABC):
            ...

        class ConcreteComponent(AbstractComponent, RegisteredComponent):
            ...

    This last approach isn't much different than just decorating your
    components with `register_component`, though.
    """

    def __init_subclass__(cls: "Type[RegisteredComponent]") -> "None":
        """
        Automagically call `register_component` on subclasses.
        """
        super().__init_subclass__()
        register_component(cls)
