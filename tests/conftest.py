# Copyright (c) 2020 Slavfox
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from typing import Callable, List, Tuple, Type, TypeVar
from types import ModuleType

import pytest
from snecs.component import Component, RegisteredComponent, register_component
from snecs.ecs import new_entity
from snecs.typedefs import EntityID
from snecs.world import World

T = TypeVar("T")


@pytest.fixture  # type: ignore[misc]
def component_a() -> Type[Component]:
    @register_component
    class AComponent(Component):
        # for easier comparing of Worlds
        def __copy__(self: T) -> T:
            return self

    return AComponent


@pytest.fixture  # type: ignore[misc]
def component_b() -> Type[Component]:
    @register_component
    class BComponent(Component):
        def __copy__(self: T) -> T:
            return self

    return BComponent


@pytest.fixture  # type: ignore[misc]
def serializable_component_a() -> Type[Component]:
    @register_component
    class SerializableComponentA(Component):
        def __init__(self, x: object):
            self.x = x

        def __copy__(self: T) -> T:
            return self

        def serialize(self) -> object:
            return self.x

        @classmethod
        def deserialize(cls, serialized: object) -> "SerializableComponentA":
            return cls(serialized)

    return SerializableComponentA


@pytest.fixture  # type: ignore[misc]
def serializable_component_b() -> Type[Component]:
    @register_component
    class SerializableComponentB(Component):
        def __init__(self, x: object, y: object):
            self.x = x
            self.y = y

        def __copy__(self: T) -> T:
            return self

        def serialize(self) -> Tuple[object, object]:
            return self.x, self.y

        @classmethod
        def deserialize(
            cls, serialized: Tuple[object, object]
        ) -> "SerializableComponentB":
            return cls(*serialized)

    return SerializableComponentB


@pytest.fixture  # type: ignore[misc]
def world() -> World:
    return World()


@pytest.fixture  # type: ignore[misc]
def empty_entity(world: World) -> EntityID:
    return new_entity(world=world)


@pytest.fixture  # type: ignore[misc]
def entity_with_cmp_a(world: World, component_a: Type[Component]) -> EntityID:
    return new_entity((component_a(),), world=world)


@pytest.fixture  # type: ignore[misc]
def missing_dunder_all_names() -> Callable[[ModuleType], List[str]]:
    def make_missing(module: ModuleType) -> List[str]:
        return [
            name
            for name in dir(module)
            if not name.startswith("_")
            and name not in ["TYPE_CHECKING"]
            and name not in module.__all__  # type: ignore[attr-defined,misc]
        ]

    return make_missing


@pytest.fixture  # type: ignore[misc]
def query_setup() -> Tuple[
    World, Tuple[Type[Component], Type[Component], Type[Component]]
]:
    world = World()

    class Cmp1(RegisteredComponent):
        pass

    class Cmp2(RegisteredComponent):
        pass

    class Cmp3(RegisteredComponent):
        pass

    for components in [
        (Cmp3, Cmp2, Cmp1),  # The first element determines the list type.
        (),
        (Cmp1,),
        (Cmp2,),
        (Cmp1, Cmp2),
        (Cmp3,),
        (Cmp3, Cmp1),
        (Cmp3, Cmp2),
    ]:
        new_entity([c() for c in components], world=world)

    return world, (Cmp1, Cmp2, Cmp3)
