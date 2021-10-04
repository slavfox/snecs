# Copyright (c) 2020 Slavfox
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2020 Slavfox
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import pytest
from esper import World as EsperWorld
from snecs.component import RegisteredComponent
from snecs.ecs import (
    add_component,
    add_components,
    delete_entity_immediately,
    has_component,
    has_components,
    new_entity,
    remove_component,
)
from snecs.query import Query
from snecs.world import World as SnecsWorld


class SnecsComponentA(RegisteredComponent):
    pass


class SnecsComponentB(RegisteredComponent):
    pass


class SnecsComponentC(RegisteredComponent):
    pass


class EsperComponentA:
    pass


class EsperComponentB:
    pass


class EsperComponentC:
    pass


@pytest.fixture  # type: ignore[misc]
def esper_world() -> EsperWorld:
    return EsperWorld()  # type: ignore[no-untyped-call]


@pytest.fixture  # type: ignore[misc]
def snecs_world() -> SnecsWorld:
    return SnecsWorld()


@pytest.mark.parametrize("backend,name", (("esper", "create_empty_entities"),))
def test_create_empty_entities_esper(esper_world, benchmark, backend, name):
    def create_entities():
        esper_world.create_entity()

    benchmark(create_entities)


@pytest.mark.parametrize("backend,name", (("snecs", "create_empty_entities"),))
def test_create_empty_entities_snecs(snecs_world, benchmark, backend, name):
    def create_entities():
        new_entity(world=snecs_world)

    benchmark(create_entities)


@pytest.mark.parametrize(
    "backend,name", (("esper", "create_entities_with_components"),)
)
def test_create_entities_with_components_esper(
    esper_world, benchmark, backend, name
):
    c1 = EsperComponentA()
    c2 = EsperComponentB()
    c3 = EsperComponentC()

    def create_entities():
        esper_world.create_entity(c1, c2, c3)

    benchmark(create_entities)


@pytest.mark.parametrize(
    "backend,name", (("snecs", "create_entities_with_components"),)
)
def test_create_entities_with_components_snecs(
    snecs_world, benchmark, backend, name
):
    c1 = SnecsComponentA()
    c2 = SnecsComponentB()
    c3 = SnecsComponentC()

    def create_entities():
        new_entity((c1, c2, c3), snecs_world)

    benchmark(create_entities)


@pytest.mark.parametrize("backend,name", (("esper", "add_component"),))
def test_add_component_esper(esper_world, benchmark, backend, name):
    def setup():
        ents = [esper_world.create_entity() for _ in range(1_000)]
        return (ents,), {}

    c = EsperComponentA()

    def esper_add_component(ents):
        for ent in ents:
            esper_world.add_component(ent, c)

    benchmark.pedantic(esper_add_component, setup=setup, rounds=2000)


@pytest.mark.parametrize("backend,name", (("snecs", "add_component"),))
def test_add_component_snecs(snecs_world, benchmark, backend, name):
    def setup():
        ents = [new_entity(world=snecs_world) for _ in range(1_000)]
        return (ents,), {}

    c = SnecsComponentA()

    def snecs_add_component(ents):
        for ent in ents:
            add_component(ent, c, snecs_world)

    benchmark.pedantic(snecs_add_component, setup=setup, rounds=2000)


@pytest.mark.parametrize("backend,name", (("esper", "add_components"),))
def test_add_components_esper(esper_world, benchmark, backend, name):
    def setup():
        ents = [esper_world.create_entity() for _ in range(1_000)]
        return (ents,), {}

    c1 = EsperComponentA()
    c2 = EsperComponentB()
    c3 = EsperComponentC()

    def esper_add_component(ents):
        for ent in ents:
            esper_world.add_component(ent, c1)
            esper_world.add_component(ent, c2)
            esper_world.add_component(ent, c3)

    benchmark.pedantic(esper_add_component, setup=setup, rounds=1000)


@pytest.mark.parametrize("backend,name", (("snecs", "add_components"),))
def test_add_components_snecs(snecs_world, benchmark, backend, name):
    def setup():
        ents = [new_entity(world=snecs_world) for _ in range(1_000)]
        return (ents,), {}

    c1 = SnecsComponentA()
    c2 = SnecsComponentB()
    c3 = SnecsComponentC()

    def snecs_add_component(ents):
        for ent in ents:
            add_components(ent, (c1, c2, c3), snecs_world)

    benchmark.pedantic(snecs_add_component, setup=setup, rounds=1000)


@pytest.mark.parametrize("backend,name", (("esper", "remove_component"),))
def test_remove_component_esper(snecs_world, benchmark, backend, name):
    c = EsperComponentA()

    def setup():
        ents = [esper_world.create_entity(c) for _ in range(1_000)]
        return (ents,), {}

    def esper_remove_component(ents):
        for ent in ents:
            esper_world.remove_component(ent, SnecsComponentA)

    benchmark.pedantic(esper_remove_component, setup=setup, rounds=2000)


@pytest.mark.parametrize("backend,name", (("snecs", "remove_component"),))
def test_remove_component_snecs(snecs_world, benchmark, backend, name):
    c = SnecsComponentA()

    def setup():
        ents = [new_entity((c,), world=snecs_world) for _ in range(1_000)]
        return (ents,), {}

    def snecs_remove_component(ents):
        for ent in ents:
            remove_component(ent, SnecsComponentA, snecs_world)

    benchmark.pedantic(snecs_remove_component, setup=setup, rounds=2000)


@pytest.mark.parametrize("backend,name", (("esper", "remove_component"),))
def test_remove_component_esper(esper_world, benchmark, backend, name):
    c = EsperComponentA()

    def setup():
        ents = [esper_world.create_entity(c) for _ in range(1_000)]
        return (ents,), {}

    def esper_remove_component(ents):
        for ent in ents:
            esper_world.remove_component(ent, EsperComponentA)

    benchmark.pedantic(esper_remove_component, setup=setup, rounds=2000)


@pytest.mark.parametrize("backend,name", (("snecs", "has_component"),))
def test_has_component_snecs(snecs_world, benchmark, backend, name):
    c1 = SnecsComponentA()
    c2 = SnecsComponentB()
    c3 = SnecsComponentC()

    ents = [
        new_entity(components, snecs_world)
        for components in [
            (),
            (c1,),
            (c2,),
            (c1, c2),
            (c3,),
            (c3, c1),
            (c3, c2),
            (c3, c2, c1),
        ]
        * 128
    ]

    def snecs_has_component():
        return [
            has_component(ent, SnecsComponentA, snecs_world) for ent in ents
        ]

    benchmark.pedantic(snecs_has_component, rounds=2000)


@pytest.mark.parametrize("backend,name", (("esper", "has_component"),))
def test_has_component_esper(esper_world, benchmark, backend, name):
    c1 = EsperComponentA()
    c2 = EsperComponentB()
    c3 = EsperComponentC()

    ents = []
    for components in [
        (),
        (c1,),
        (c2,),
        (c1, c2),
        (c3,),
        (c3, c1),
        (c3, c2),
        (c3, c2, c1),
    ] * 128:
        entid = esper_world.create_entity(*components)
        if components == ():
            # Have to do this manually, because Esper currently has a bug
            # and won't register entities until they have a component
            # added. Doing any operation other than adding components on a
            # componentless entity will crash, unless we do this
            # explicitly:
            esper_world._entities[entid] = {}
        ents.append(entid)

    def esper_has_component():
        return [
            esper_world.has_component(ent, EsperComponentA) for ent in ents
        ]

    benchmark(esper_has_component)


@pytest.mark.parametrize("backend,name", (("snecs", "has_components"),))
def test_has_components_snecs(snecs_world, benchmark, backend, name):
    c1 = SnecsComponentA()
    c2 = SnecsComponentB()
    c3 = SnecsComponentC()

    ents = [
        new_entity(components, snecs_world)
        for components in [
            (),
            (c1,),
            (c2,),
            (c1, c2),
            (c3,),
            (c3, c1),
            (c3, c2),
            (c3, c2, c1),
        ]
        * 128
    ]

    def snecs_has_components():
        return [
            has_components(
                ent, (SnecsComponentA, SnecsComponentC), snecs_world
            )
            for ent in ents
        ]

    benchmark(snecs_has_components)


@pytest.mark.parametrize("backend,name", (("esper", "has_components"),))
def test_has_components_esper(esper_world, benchmark, backend, name):
    c1 = EsperComponentA()
    c2 = EsperComponentB()
    c3 = EsperComponentC()

    ents = []
    for components in [
        (),
        (c1,),
        (c2,),
        (c1, c2),
        (c3,),
        (c3, c1),
        (c3, c2),
        (c3, c2, c1),
    ] * 128:
        entid = esper_world.create_entity(*components)
        if components == ():
            # Have to do this manually, because Esper currently has a bug
            # and won't register entities until they have a component
            # added. Doing any operation other than adding components on a
            # componentless entity will crash, unless we do this
            # explicitly:
            esper_world._entities[entid] = {}
        ents.append(entid)

    def esper_has_components():
        return [
            esper_world.has_components(ent, EsperComponentA, EsperComponentC)
            for ent in ents
        ]

    benchmark(esper_has_components)


@pytest.mark.parametrize(
    "backend,name", (("esper", "delete_empty_entity_immediate"),)
)
def test_delete_empty_entity_immediate_esper(
    esper_world, benchmark, backend, name
):
    def setup():
        ents = []
        for _ in range(1_000):
            ent_id = esper_world.create_entity()
            ents.append(ent_id)
            esper_world._entities[ent_id] = {}
        return (ents,), {}

    def esper_delete(ents):
        for ent in ents:
            esper_world.delete_entity(ent, immediate=True)

    benchmark.pedantic(esper_delete, setup=setup, rounds=1000)


@pytest.mark.parametrize(
    "backend,name", (("snecs", "delete_empty_entity_immediate"),)
)
def test_delete_empty_entity_immediate_snecs(
    snecs_world, benchmark, backend, name
):
    def setup():
        ents = [new_entity(world=snecs_world) for _ in range(1_000)]
        return (ents,), {}

    def snecs_delete(ents):
        for ent in ents:
            delete_entity_immediately(ent, snecs_world)

    benchmark.pedantic(snecs_delete, setup=setup, rounds=1000)


@pytest.mark.parametrize(
    "backend,name", (("esper", "delete_entity_with_components_immediate"),)
)
def test_delete_entity_with_components_immediate_esper(
    esper_world, benchmark, backend, name
):

    c1 = EsperComponentA()
    c2 = EsperComponentB()
    c3 = EsperComponentC()

    def setup():
        ents = [esper_world.create_entity(c1, c2, c3) for _ in range(1_000)]
        return (ents,), {}

    def esper_delete(ents):
        for ent in ents:
            esper_world.delete_entity(ent, immediate=True)

    benchmark.pedantic(esper_delete, setup=setup, rounds=1000)


@pytest.mark.parametrize(
    "backend,name", (("snecs", "delete_entity_with_components_immediate"),)
)
def test_delete_entity_with_components_immediate_snecs(
    snecs_world, benchmark, backend, name
):

    c1 = SnecsComponentA()
    c2 = SnecsComponentB()
    c3 = SnecsComponentC()

    def setup():
        ents = [
            new_entity((c1, c2, c3), world=snecs_world) for _ in range(1_000)
        ]
        return (ents,), {}

    def snecs_delete(ents):
        for ent in ents:
            delete_entity_immediately(ent, snecs_world)

    benchmark.pedantic(snecs_delete, setup=setup, rounds=1000)


@pytest.mark.parametrize("backend,name", (("snecs", "component_lookup"),))
def test_component_lookups_compiled_snecs(
    snecs_world, benchmark, backend, name
):
    c1 = SnecsComponentA()
    c2 = SnecsComponentB()
    c3 = SnecsComponentC()

    ents = [
        new_entity(components, snecs_world)
        for components in [
            (),
            (c1,),
            (c2,),
            (c1, c2),
            (c3,),
            (c3, c1),
            (c3, c2),
            (c3, c2, c1),
        ]
        * 128
    ]
    q = Query((SnecsComponentA, SnecsComponentC), snecs_world).compile()

    def snecs_has_components():
        return [result for result in q]

    benchmark(snecs_has_components)


@pytest.mark.parametrize("backend,name", (("snecs", "component_lookup"),))
def test_component_lookups_dynamic_snecs(
    snecs_world, benchmark, backend, name
):
    c1 = SnecsComponentA()
    c2 = SnecsComponentB()
    c3 = SnecsComponentC()

    ents = [
        new_entity(components, snecs_world)
        for components in [
            (),
            (c1,),
            (c2,),
            (c1, c2),
            (c3,),
            (c3, c1),
            (c3, c2),
            (c3, c2, c1),
        ]
        * 128
    ]

    def snecs_has_components():
        return [
            result
            for result in Query(
                (SnecsComponentA, SnecsComponentC), snecs_world
            )
        ]

    benchmark(snecs_has_components)


@pytest.mark.parametrize("backend,name", (("esper", "component_lookup"),))
def test_component_lookups_esper(esper_world, benchmark, backend, name):
    c1 = EsperComponentA()
    c2 = EsperComponentB()
    c3 = EsperComponentC()

    ents = []
    for components in [
        (),
        (c1,),
        (c2,),
        (c1, c2),
        (c3,),
        (c3, c1),
        (c3, c2),
        (c3, c2, c1),
    ] * 128:
        entid = esper_world.create_entity(*components)
        if components == ():
            # Have to do this manually, because Esper currently has a bug
            # and won't register entities until they have a component
            # added. Doing any operation other than adding components on a
            # componentless entity will crash, unless we do this
            # explicitly:
            esper_world._entities[entid] = {}
        ents.append(entid)

    def esper_has_components():
        return [
            result
            for result in esper_world.get_components(
                EsperComponentA, EsperComponentC
            )
        ]

    benchmark(esper_has_components)
