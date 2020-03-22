# Copyright (c) 2020 Slavfox
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import pytest
from snecs.component import (
    Component,
    RegisteredComponent,
    _component_names,
    _component_registry,
    register_component,
)


def test_component_no_overrides_correct():
    @register_component
    class MyComponent(Component):
        pass

    assert _component_registry[MyComponent] == MyComponent._bitmask


def test_component_serializable():
    @register_component
    class Serializable(Component):
        def serialize(self):
            pass

        @classmethod
        def deserialize(cls, serialized):
            pass

    assert _component_registry[Serializable] == Serializable._bitmask


def test_component_overrides_serialize_only():
    class BadComponent(Component):
        def serialize(self):
            pass

    with pytest.raises(TypeError, match=r"does not override `deserialize"):
        register_component(BadComponent)


def test_component_overrides_deserialize_only():
    class BadComponent(Component):
        @classmethod
        def deserialize(cls, serialized):
            pass

    with pytest.raises(TypeError, match="does not override `serialize"):
        register_component(BadComponent)


def test_component_register_twice():
    @register_component
    class AlreadyRegistered(Component):
        pass

    with pytest.raises(ValueError, match="already registered"):
        register_component(AlreadyRegistered)


def test_component_same_name():
    @register_component
    class SameName(Component):
        pass

    a = SameName

    @register_component
    class SameName(Component):
        pass

    b = SameName

    assert _component_registry[a] == a._bitmask
    assert _component_registry[b] == b._bitmask


def test_component_same_name_serializable():
    @register_component
    class NonUniqueName(Component):
        def serialize(self):
            pass

        @classmethod
        def deserialize(cls, val):
            pass

    a = NonUniqueName

    class NonUniqueName(Component):
        def serialize(self):
            pass

        @classmethod
        def deserialize(cls, val):
            pass

    with pytest.raises(ValueError, match="non-unique name"):
        register_component(NonUniqueName)


def test_registeredcomponent():
    class Registered(RegisteredComponent):
        pass

    assert _component_registry[Registered] == Registered._bitmask
