# Copyright (c) 2020, Slavfox
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import re
from typing import Type
from types import new_class

import pytest
from snecs._detail import Bitmask
from snecs.component import Component
from snecs.filters import AndExpr, NotExpr, OrExpr, compile_filter, matches


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
        # simple
        (A, A),
        # not
        (~A, NotExpr(A)),
        (~(~A), A),
        # and
        (A & A, A),
        (A & B, AndExpr(A, B)),
        ((A & B) & C, AndExpr(A, B, C)),
        (A & (B & C), AndExpr(A, B, C)),
        ((A & B & A), AndExpr(A, B)),
        ((A & A & A), A),
        ((A & (A & A)), A),
        # De Morgan's 1st law
        (~(A & B), OrExpr(~A, ~B)),
        # or
        ((A | A), A),
        (((A | A) | A), A),
        ((A | (A | A)), A),
        ((A | A), A),
        (A & (B | C), AndExpr(A, OrExpr(B, C))),
        ((A | B) & C, AndExpr(OrExpr(A, B), C)),
        (~(A | A), NotExpr(A)),
        (~(A | ~B), AndExpr(B, NotExpr(A))),
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
        ((A | B) & (~A | C), 0b_0000_0000, False),
        ((A | B) & (~A | C), 0b_0000_0001, False),
        ((A | B) & (~A | C), 0b_0000_0010, True),
        ((A | B) & (~A | C), 0b_0000_0011, False),
        ((A | B) & (~A | C), 0b_0000_0100, False),
        ((A | B) & (~A | C), 0b_0000_0101, True),
        ((A | B) & (~A | C), 0b_0000_0110, True),
        ((A | B) & (~A | C), 0b_0000_0111, True),
    ],
)
def test_matching(expr, bitmask, should_match):
    assert matches(expr, bitmask) == should_match
    match = compile_filter(expr)
    assert match @ bitmask == should_match


@pytest.mark.parametrize(
    "expr, clauses",
    [
        (~A, {"0"}),
        (A & ~A, set()),
        (A & B, {"11"}),
        (A & B & C, {"111"}),
        (A | B, {".1", "1."}),
        (A | B | C, {"..1", ".1.", "1.."}),
        ((A & B) | C, {".11", "1.."}),
        ((A & B) | (C & D), {"..11", "11.."}),
        ((A | B) & (~A | C), {"1.1", ".10", "11."}),
        (~(~A & ~B), {"1.", ".1"}),
        (~(A | B), {"00"}),
        (~(A & B), {"0.", ".0"}),
        (A | ~A, {"."}),
        ((A & ~B) | (~A & B), {"01", "10"}),
    ],
)
def test_clauses(expr, clauses):
    matcher = expr._make_compiler()
    assert set(matcher._pretty_clauses()) == clauses
    compiled = matcher.compile()
    if not clauses:
        assert not compiled.matches(Bitmask(1))
        assert not compiled.matches(Bitmask(0))
    else:
        l = len(next(iter(clauses)))
        for i in range(1 << l):
            i_str = f"{i:b}".zfill(l)
            should_match = any(re.match(clause, i_str) for clause in clauses)

            assert compiled.matches(Bitmask(i)) == should_match


@pytest.mark.parametrize(
    "expr, s",
    [
        (~A, "CompiledFilter[~A]"),
        (A & ~A, "CompiledFilter[A & (~A)]"),
        (A & B, "CompiledFilter[A & B]"),
        (A & B & C, "CompiledFilter[A & B & C]"),
        (A | B, "CompiledFilter[A | B]"),
        (A | B | C, "CompiledFilter[A | B | C]"),
        ((A & B) | C, "CompiledFilter[(A & B) | C]"),
        ((A & B) | (C & D), "CompiledFilter[(A & B) | (C & D)]"),
        ((A | B) & (~A | C), "CompiledFilter[(A | B) & ((~A) | C)]"),
        (~(~A & ~B), "CompiledFilter[A | B]"),
        (~(A | B), "CompiledFilter[(~A) & (~B)]"),
        (~(A & B), "CompiledFilter[(~A) | (~B)]"),
        (A | ~A, "CompiledFilter[true]"),
        ((A & ~B) | (~A & B), "CompiledFilter[(A & (~B)) | ((~A) & B)]"),
    ],
)
def test_filter_str(expr, s):
    assert str(compile_filter(expr)) == s


@pytest.mark.parametrize(
    "expr, s",
    [
        (~A, "~A"),
        (A & ~A, "A & (~A)"),
        (A & B, "A & B"),
        (A & B & C, "A & B & C"),
        (A | B, "A | B"),
        (A | B | C, "A | B | C"),
        ((A & B) | C, "(A & B) | C"),
        ((A & B) | (C & D), "(A & B) | (C & D)"),
        ((A | B) & (~A | C), "(A | B) & ((~A) | C)"),
        (~(~A & ~B), "A | B"),
        (~(A | B), "(~A) & (~B)"),
        (~(A & B), "(~A) | (~B)"),
        (A | ~A, "true"),
        ((A & ~B) | (~A & B), "(A & (~B)) | ((~A) & B)"),
    ],
)
def test_filter_str(expr, s):
    assert str(expr) == s
