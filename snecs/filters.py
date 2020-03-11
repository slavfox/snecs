"""
Query filtering tools.
"""
from typing import TYPE_CHECKING, Union
from abc import ABC, abstractmethod
from functools import reduce
from operator import and_, inv, or_

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

    _Selector = Bitmask
    _ValueMask = Bitmask
    _MatcherCombinerType = Callable[["Matcher", "Matcher"], "Matcher"]

Term = Union["Expr", "ComponentMeta"]


def compile_filter(term: "Term") -> "Callable[[Bitmask], bool]":
    if isinstance(term, Expr):
        return term._make_matcher().compile()
    term_bitmask = term._bitmask

    def match(bitmask: "Bitmask") -> bool:
        return bool(bitmask & term_bitmask)

    return match


def _format_expr_term(term: "Term") -> str:
    if isinstance(term, Expr):
        return repr(term)
    else:
        return term.__name__


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
                #       (...|a) & (...|~a).
                new_clauses.append(
                    ((lselector | rselector), (lvaluemask | rvaluemask))
                )
        return Matcher(new_clauses)

    def __or__(self, other: "Matcher") -> "Matcher":
        return Matcher([*self.clauses, *other.clauses])

    def __invert__(self) -> "Matcher":
        # Todo: since (~a & ~b) matches against 00, ~(~a & ~b) matches against
        #       11. This is extremely wrong.
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
    __slots__ = ()

    @abstractmethod
    def _make_matcher(self) -> "Matcher":
        ...


class StaticExpr(Expr, ABC):  # noqa: W0223
    #                           "Method '_make_matcher' is abstract in class
    #                           'Expr' but is not overridden."
    #                           A false positive from, to nobody's surprise,
    #                           pylint. StaticExpr is an abstract class,
    #                           so it doesn't have to override _make_matcher.
    __slots__ = ()
    _retval: "bool" = False

    def __repr__(self) -> "str":
        return str(self._retval).lower()


class _TrueExpr(StaticExpr):
    __slots__ = ()
    _retval = True

    def __invert__(self) -> "_FalseExpr":
        return FalseExpr

    def _make_matcher(self) -> "Matcher":
        # Anything & 0 == 0
        return Matcher(clauses=[(Bitmask(0), Bitmask(0))])


class _FalseExpr(StaticExpr):
    __slots__ = ()
    _retval = False

    def __invert__(self) -> "_TrueExpr":
        return TrueExpr

    def _make_matcher(self) -> "Matcher":
        # any([]) == False
        return Matcher(clauses=[])


TrueExpr = _TrueExpr()
FalseExpr = _FalseExpr()


class DynamicExpr(Expr, ABC):
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
            return other.__rand__(self)
        return AndExpr(self, other)

    def __rand__(self, other: "Term") -> "AndExpr":
        if isinstance(other, AndExpr):
            return other & self
        return AndExpr(other, self)

    def __or__(self, other: "Term") -> "OrExpr":
        if isinstance(other, OrExpr):
            return other.__ror__(self)
        return OrExpr(self, other)

    def __ror__(self, other: "Term") -> "OrExpr":
        if isinstance(other, OrExpr):
            return other | self
        return OrExpr(self, other)

    def __invert__(self) -> "Term":
        return NotExpr(self)

    def __repr__(self) -> "str":
        return (
            f"({self._operator_repr} "
            f"{' '.join(_format_expr_term(t) for t in self.terms)})"
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

    def __hash__(self) -> int:
        return hash((self.__class__, self.terms))

    def __eq__(self, other: "object") -> bool:
        return isinstance(other, self.__class__) and set(other.terms) == set(
            self.terms
        )


class NotExpr(DynamicExpr):
    """
    A "not" expression: `~Term`.

    Matches bitmasks where all the bits from ``Term._bitmask`` are zero.
    """

    __slots__ = ()
    _operator_repr = "~"

    def __init__(self, term: "Term") -> "None":  # noqa: W0235
        # W0235: "Useless super delegation in method '__init__'"
        # Actually not useless, because NotExpr.__init__ is not variadic.
        super().__init__(term)

    def _get_component_matcher(self, term: "ComponentMeta") -> Matcher:
        return Matcher(clauses=[(term._bitmask, ZERO)])

    def _extend_matcher(self, matcher: "Matcher") -> "Matcher":
        return ~matcher

    def __invert__(self) -> "Term":
        return self.terms[0]


class MultiExpr(DynamicExpr, ABC):
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
            return AndExpr(*self.terms, *other.terms)
        return AndExpr(*self.terms, other)

    def __rand__(self, other: "Term") -> "AndExpr":
        if isinstance(other, AndExpr):
            return AndExpr(*other.terms, *self.terms)
        return AndExpr(other, *self.terms)


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
            return OrExpr(*self.terms, *other.terms)
        return OrExpr(*self.terms, other)

    def __ror__(self, other: "Term") -> "OrExpr":
        if isinstance(other, AndExpr):
            return OrExpr(*other.terms, *self.terms)
        return OrExpr(other, *self.terms)

    # noinspection PyUnboundLocalVariable
    def __invert__(self) -> "AndExpr":
        inv: "Callable[[Term], Term]"  # noqa: W0621
        # De Morgan's 2nd law
        return AndExpr(*map(inv, self.terms))
