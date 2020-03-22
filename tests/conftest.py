# Copyright (c) 2020 Slavfox
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import pytest
from snecs.component import Component, RegisteredComponent, register_component
from snecs.ecs import new_entity
from snecs.world import World


@pytest.fixture
def component_a():
    @register_component
    class AComponent(Component):
        # for easier comparing of Worlds
        def __copy__(self):
            return self

    return AComponent


@pytest.fixture
def component_b():
    @register_component
    class BComponent(Component):
        def __copy__(self):
            return self

    return BComponent


@pytest.fixture
def serializable_component_a():
    @register_component
    class SerializableComponentA(Component):
        def __init__(self, x):
            self.x = x

        def __copy__(self):
            return self

        def serialize(self):
            return self.x

        @classmethod
        def deserialize(cls, serialized):
            return cls(serialized)

    return SerializableComponentA


@pytest.fixture
def serializable_component_b():
    @register_component
    class SerializableComponentB(Component):
        def __init__(self, x, y):
            self.x = x
            self.y = y

        def __copy__(self):
            return self

        def serialize(self):
            return self.x, self.y

        @classmethod
        def deserialize(cls, serialized):
            return cls(*serialized)

    return SerializableComponentB


@pytest.fixture
def world():
    return World()


@pytest.fixture
def empty_entity(world):
    return new_entity(world=world)


@pytest.fixture
def entity_with_cmp_a(world, component_a):
    return new_entity((component_a(),), world=world)


@pytest.fixture
def missing_dunder_all_names():
    def make_missing(module):
        return [
            name
            for name in dir(module)
            if not name.startswith("_")
            and name not in ["TYPE_CHECKING"]
            and name not in module.__all__
        ]

    return make_missing


@pytest.fixture
def query_setup():
    world = World()

    class Cmp1(RegisteredComponent):
        pass

    class Cmp2(RegisteredComponent):
        pass

    class Cmp3(RegisteredComponent):
        pass

    for components in [
        (),
        (Cmp1,),
        (Cmp2,),
        (Cmp1, Cmp2),
        (Cmp3,),
        (Cmp3, Cmp1),
        (Cmp3, Cmp2),
        (Cmp3, Cmp2, Cmp1),
    ]:
        new_entity([c() for c in components], world=world)

    return world, (Cmp1, Cmp2, Cmp3)
