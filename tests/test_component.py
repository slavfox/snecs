# Copyright (c) 2020 Slavfox
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import pytest
from snecs.component import (
    Component,
    RegisteredComponent,
    _component_registry,
    register_component,
)


def test_component_no_overrides_correct() -> None:
    @register_component
    class MyComponent(Component):
        pass

    assert _component_registry[MyComponent] == MyComponent._bitmask


def test_component_serializable() -> None:
    @register_component
    class Serializable(Component):
        def serialize(self) -> None:
            pass

        @classmethod
        def deserialize(cls, serialized: None) -> "Serializable":
            return cls()

    assert _component_registry[Serializable] == Serializable._bitmask


def test_component_overrides_serialize_only() -> None:
    class BadComponent(Component):
        def serialize(self) -> None:
            pass

    with pytest.raises(TypeError, match=r"does not override `deserialize"):
        register_component(BadComponent)


def test_component_overrides_deserialize_only() -> None:
    class BadComponent(Component):
        @classmethod
        def deserialize(cls, serialized: None) -> "BadComponent":
            return cls()

    with pytest.raises(TypeError, match="does not override `serialize"):
        register_component(BadComponent)


def test_component_register_twice() -> None:
    @register_component
    class AlreadyRegistered(Component):
        pass

    with pytest.raises(ValueError, match="already registered"):
        register_component(AlreadyRegistered)


def test_component_same_name() -> None:
    @register_component
    class SameName(Component):
        pass

    a = SameName

    @register_component
    class SameName(Component):  # type: ignore[no-redef]
        pass

    b = SameName

    assert _component_registry[a] == a._bitmask
    assert _component_registry[b] == b._bitmask


def test_component_same_name_serializable() -> None:
    @register_component
    class NonUniqueName(Component):
        def serialize(self) -> None:
            pass

        @classmethod
        def deserialize(cls, val: None) -> "NonUniqueName":
            return cls()

    a = NonUniqueName

    class NonUniqueName(Component):  # type: ignore[no-redef]
        def serialize(self) -> None:
            pass

        @classmethod
        def deserialize(  # type: ignore[override]
            cls, val: None
        ) -> "NonUniqueName":
            return cls()  # type: ignore[return-value]

    with pytest.raises(ValueError, match="non-unique name"):
        register_component(NonUniqueName)


def test_registeredcomponent() -> None:
    class Registered(RegisteredComponent):
        pass

    assert _component_registry[Registered] == Registered._bitmask
