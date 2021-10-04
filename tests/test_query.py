# Copyright (c) 2020 Slavfox
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from typing import Tuple, Type

from snecs.component import Component
from snecs.ecs import has_component
from snecs.query import Query
from snecs.world import World

QuerySetup = Tuple[
    World, Tuple[Type[Component], Type[Component], Type[Component]]
]


def test_query(query_setup: QuerySetup) -> None:
    world, (cmp1, cmp2, cmp3) = query_setup

    results = []
    for ent, components in Query([cmp1], world=world):
        results.append(ent)
        assert cmp1 in {c.__class__ for c in components}

    assert results


def test_query_empty(query_setup: QuerySetup) -> None:
    world, _ = query_setup
    assert list(Query([], world=world)) == []


def test_query_empty_compile(query_setup: QuerySetup) -> None:
    world, _ = query_setup
    q = Query([], world=world).compile()
    assert list(q) == []


def test_query_filter(query_setup: QuerySetup) -> None:
    world, (cmp1, cmp2, cmp3) = query_setup

    results = []
    for ent, components in Query([cmp1], world=world).filter(cmp3):
        results.append(ent)
        assert cmp1 in {c.__class__ for c in components}
        assert has_component(ent, cmp3, world=world)

    assert results


def test_query_compile(query_setup: QuerySetup) -> None:
    world, (cmp1, cmp2, cmp3) = query_setup

    results = []
    q = Query([cmp1], world=world).compile()
    for ent, components in q:
        results.append(ent)
        assert cmp1 in {c.__class__ for c in components}

    assert results


def test_query_filter_compile(query_setup: QuerySetup) -> None:
    world, (cmp1, cmp2, cmp3) = query_setup

    results = []
    q = Query([cmp1], world=world).filter(cmp3 & ~cmp2).compile()
    for ent, components in q:
        results.append(ent)
        assert cmp1 in {c.__class__ for c in components}
        assert has_component(ent, cmp3, world=world)
        assert not has_component(ent, cmp2, world=world)

    assert results
