# Copyright (c) 2020, Slavfox
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import pytest
from typing import Type
from types import new_class
from snecs.component import Component
from snecs.filters import AndExpr, OrExpr, NotExpr, compile_filter


def make_component_class(name, bitmask) -> Type[Component]:
    cls = new_class(name, (Component,))
    cls._bitmask = bitmask
    # noinspection PyTypeChecker
    return cls


A = make_component_class("A", 0b_0000_0001)
B = make_component_class("B", 0b_0000_0010)
C = make_component_class("C", 0b_0000_0100)
D = make_component_class("D", 0b_0000_1000)


@pytest.mark.parametrize(
    "expr,expected_type,expected_terms",
    [
        # and
        (A & B, AndExpr, (A, B)),
        (A & (B & C), AndExpr, (A, B, C)),
        ((A & B) & C, AndExpr, (A, B, C)),
        ((A & B) & (C & D), AndExpr, (A, B, C, D)),
        # or
        (A | B, OrExpr, (A, B)),
        (A | (B | C), OrExpr, (A, B, C)),
        ((A | B) | C, OrExpr, (A, B, C)),
        ((A | B) | (C | D), OrExpr, (A, B, C, D)),
        # not
        (~A, NotExpr, (A,)),
    ],
)
def test_expression_builder_simple(expr, expected_type, expected_terms):
    assert isinstance(expr, expected_type)
    assert expr.terms == expected_terms


@pytest.mark.parametrize(
    "expr,expected_terms",
    [
        (A & (B | C), AndExpr(A, OrExpr(B, C))),
        ((A | B) & C, AndExpr(OrExpr(A, B), C)),
        # De Morgan's 2nd law
        (~(A | B), AndExpr(NotExpr(A), NotExpr(B))),
    ],
)
def test_complex_expression_builder(expr, expected_terms):
    assert expr == expected_terms


@pytest.mark.parametrize(
    "expr, bitmask, should_match",
    [
        (A, 0b_0000_0000, False),
        (A, 0b_0000_0001, True),
        (A, 0b_0000_0010, False),
        (A, 0b_0000_0011, True),
        (A, 0b_1111_1111, True),
        (A, 0b_1111_1110, False),
        (~A, 0b_0000_0000, True),
        (~A, 0b_0000_0001, False),
        (~A, 0b_0000_0010, True),
        (~A, 0b_0000_0011, False),
        (~A, 0b_1111_1111, False),
        (~A, 0b_1111_1110, True),
        (A & ~A, 0b_0000_0000, False),
        (A & ~A, 0b_0000_0001, False),
        (A | B, 0b_0000_0000, False),
        (A | B, 0b_0000_0001, True),
        (A | B, 0b_0000_0010, True),
        (A | B, 0b_0000_0011, True),
        (A | B, 0b_1111_1111, True),
        (A | B, 0b_1111_1110, True),
        (A | B, 0b_1111_1100, False),
        (A & B, 0b_0000_0000, False),
        (A & B, 0b_0000_0001, False),
        (A & B, 0b_0000_0010, False),
        (A & B, 0b_0000_0011, True),
        (A & B, 0b_1111_1111, True),
        (A & B, 0b_1111_1110, False),
        (A & B & C, 0b_0000_0000, False),
        (A & B & C, 0b_0000_0001, False),
        (A & B & C, 0b_0000_0010, False),
        (A & B & C, 0b_0000_0011, False),
        (A & B & C, 0b_0000_0100, False),
        (A & B & C, 0b_0000_0111, True),
        (A & B & C, 0b_1111_1111, True),
        (A & B & C, 0b_1111_1110, False),
        ((A & B) | C, 0b_0000_0000, False),
        ((A & B) | C, 0b_0000_0001, False),
        ((A & B) | C, 0b_0000_0010, False),
        ((A & B) | C, 0b_0000_0011, True),
        ((A & B) | C, 0b_0000_0100, True),
        ((A & B) | C, 0b_0000_0111, True),
        ((A & B) | C, 0b_1111_1111, True),
        ((A & B) | C, 0b_1111_1110, True),
    ],
)
def test_matching(expr, bitmask, should_match):
    match = compile_filter(expr)
    assert match(bitmask) == should_match
