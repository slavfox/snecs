"""
Query filtering tools.
"""
from typing import TYPE_CHECKING, TypeVar, Union
from abc import ABC
from functools import reduce
from operator import and_, or_

from snecs._detail import ZERO, Bitmask

if TYPE_CHECKING:
    from typing import Callable, Tuple, Iterable, ClassVar

    # The ComponentMeta import is detected by both PyCharm and flake8 as
    # unused, but it *is* used - literally on the next line. To be fair,
    # detecting this kind of use is really hard to do without false positives,
    # so we're exempting this line from linting explicitly.
    #
    # noinspection PyUnresolvedReferences
    from snecs.component import ComponentMeta  # noqa

Term = Union["Expr", "ComponentMeta"]

Signature = TypeVar("Signature", bound="Tuple[Term, ...]")
_Selector = Bitmask
_ValueMask = Bitmask
_MatcherCombinerType = Callable[["Matcher", "Matcher"], "Matcher"]


class Matcher:
    def __init__(
        self, clauses: "Iterable[Tuple[_Selector, _ValueMask]]"
    ) -> None:
        # Sanity check to trim out ignored bits, so that eg.
        #
        #   selector:   0b_0110
        #   value_mask: 0b_1111
        #
        # doesn't break `bitmask & selector == valuemask`
        self.clauses = [
            (selector, selector & valuemask) for selector, valuemask in clauses
        ]

    def __and__(self, other: "Matcher") -> "Matcher":
        new_clauses = []
        for lselector, lvaluemask in self.clauses:
            for rselector, rvaluemask in other.clauses:
                # ToDo: I'm pretty sure this has a bug for
                # Todo: (...|a) & (...|~a).
                new_clauses.append(
                    ((lselector | rselector), (lvaluemask | rvaluemask))
                )
        return Matcher(new_clauses)

    def __or__(self, other: "Matcher") -> "Matcher":
        return Matcher([*self.clauses, *other.clauses])

    def __invert__(self) -> "Matcher":
        return Matcher(
            [(selector, ~valuemask) for selector, valuemask in self.clauses]
        )

    def compile(self) -> "Callable[[Bitmask], bool]":
        clauses = self.clauses

        def match(bitmask: "Bitmask") -> bool:
            return any(
                bitmask & selector == valuemask
                for selector, valuemask in clauses
            )

        return match


class Expr(ABC):
    """
    Base abstract class for filter expressions.

    Represents an unary expression, with a single operand.
    """

    __slots__ = ("matcher", "terms")
    _operator_repr: "ClassVar[str]" = "Expr"
    _matcher_combiner: "ClassVar[_MatcherCombinerType]" = and_

    def _make_matcher(self) -> "Matcher":
        return reduce(
            # see: https://github.com/python/mypy/issues/5485
            self._matcher_combiner,  # type: ignore
            (self._make_matcher_for(term) for term in self.terms),
        )

    def __init__(self, *terms: "Term"):
        self.terms: "Tuple[Term, ...]" = terms

    def __and__(self, other: "Term") -> "AndExpr":
        if isinstance(other, AndExpr):
            return other & self
        return AndExpr(other, self)

    def __or__(self, other: "Term") -> "OrExpr":
        if isinstance(other, OrExpr):
            return other | self
        return OrExpr(other, self)

    def __invert__(self) -> "NotExpr":
        return NotExpr(self)

    def __repr__(self) -> "str":
        return (
            f"({self._operator_repr} {' '.join(repr(t) for t in self.terms)})"
        )

    def _make_matcher_for(self, term: "Term") -> "Matcher":
        if isinstance(term, Expr):
            return self._extend_matcher(term._make_matcher())
        else:
            return self._get_component_matcher(term)

    def _get_component_matcher(self, term: "ComponentMeta") -> "Matcher":
        return Matcher(clauses=[(term._bitmask, term._bitmask)])

    def _extend_matcher(self, matcher: "Matcher") -> "Matcher":
        return matcher


class NotExpr(Expr):
    """
    A "not" expression: `~Term`.

    Matches bitmasks where all the bits from ``Term._bitmask`` are zero.
    """

    __slots__ = ()
    _operator_repr = "~"

    def __init__(self, term: "Term") -> "None":
        super().__init__(term)

    def _get_component_matcher(self, term: "ComponentMeta") -> Matcher:
        return Matcher(clauses=[(term._bitmask, ZERO)])

    def _extend_matcher(self, matcher: "Matcher") -> "Matcher":
        return ~matcher


class MultiExpr(Expr, ABC):
    """
    An abstract base class for 2+-ary expressions, like ``X & Y & Z``.
    """

    __slots__ = ()
    _operator_repr = "MultiExpr"


class AndExpr(MultiExpr):
    """
    An "and" expression: ``X & Y``.

    Matches bitmasks matched by all of its operands.
    """

    __slots__ = ()
    _operator_repr = "&"

    def __and__(self, other: "Term") -> "AndExpr":
        if isinstance(other, AndExpr):
            return AndExpr(*(self.terms + other.terms))
        return AndExpr(self, other)


class OrExpr(MultiExpr):
    """
    An "or" expression: ``X & Y``.

    Matches bitmasks matched by any of its operands.
    """

    __slots__ = ()
    _operator_repr = "|"
    _matcher_combiner: "ClassVar[_MatcherCombinerType]" = or_

    def __or__(self, other: "Term") -> "OrExpr":
        if isinstance(other, OrExpr):
            return OrExpr(*(self.terms + other.terms))
        return OrExpr(self, other)
