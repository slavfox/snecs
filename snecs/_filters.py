"""
Query filtering tools.

Effectively a boolean algebra system on bitvectors.
"""
from typing import TYPE_CHECKING, Callable
from abc import ABC, abstractmethod
from functools import reduce
from operator import and_, or_

from snecs._detail import ZERO, Bitmask

if TYPE_CHECKING:
    from typing import (
        Tuple,
        Sequence,
        ClassVar,
        TypeVar,
        List,
        Union,
        NoReturn,
    )

    from snecs.component import ComponentMeta

    _Selector = Bitmask
    _ValueMask = Bitmask
    _MatcherCombinerType = Callable[
        ["ExprCompiler", "ExprCompiler"], "ExprCompiler"
    ]
    _BoolLike = Union["int", "bool"]
    _CompiledMatcherType = Callable[[Bitmask], _BoolLike]

    T = TypeVar("T")
    Term = Union["Expr", "ComponentMeta"]

    # make inv pass type checking
    def inv(term: "Term") -> "Term":  # noqa
        ...


else:
    from operator import inv


__all__ = ["compile_filter"]


class NonliteralTerm(ABC):
    __slots__ = ()

    @abstractmethod
    def matches(self, bitmask: "Bitmask") -> "_BoolLike":
        ...


class CompiledFilter(NonliteralTerm, ABC):
    __slots__ = ("_expr",)

    def __init__(self, ex: "str") -> "None":
        self._expr = ex

    def __repr__(self) -> "str":
        return f"CompiledFilter[{self._expr}]"


def compile_filter(term: "Term") -> "CompiledFilter":
    """
    Compile a filter into a much faster function (Bitmask) -> `bool`.

    :param term: Filter expression to compile
    :return: a function taking a Bitmask and returning `True` if it
             matches the filter and `False` if it doesn't.
    """
    if isinstance(term, Expr):
        return term._make_compiler().compile(str(term))
    # else
    term_bitmask = term._bitmask

    # This is ugly and all, but we're doing this the ugly way for maximum
    # performance; staticmethod is a descriptor, so it adds a little bit of
    # overhead to the name lookup, so calling filter.matches() is slower
    # than normal methods. OTOH, when saving it to an intermediate variable:
    #
    #     matches = filter.matches
    #     for ... in ...:
    #         if matches(...): ...
    #
    # staticmethod and an external function are about on par, with normal
    # methods being slowest. Since the external function is the fastest in
    # both cases, that's what we use - but we define an unused first argument
    # to keep the signature correct.
    def match(_: object, bitmask: "Bitmask") -> "_BoolLike":
        # calling bool() on this to hit the fast-path for booleans is not
        # worth the function call overhead.
        return bitmask & term_bitmask

    class Filter(CompiledFilter):
        __slots__ = ()
        matches: "_CompiledMatcherType" = match  # type: ignore

    return Filter(term.__name__)


def matches(
    term: "Union[Term, CompiledFilter]", bitmask: "Bitmask"
) -> "_BoolLike":
    """
    Check if a filter expression matches a bitmask.

    :param term: The expression to match the bitmask against
    :param bitmask: Bitmask to match
    """
    if isinstance(term, NonliteralTerm):
        return term.matches(bitmask)
    else:
        return bitmask & term._bitmask


def _format_expr_term(term: "Term") -> str:
    if isinstance(term, Expr):
        return f"({str(term)})"
    else:
        return term.__name__


class ExprCompiler:
    """
    A compiler for an expression tree.

    ExprCompiler represents an arbitrary expression tree as a flat list of
    pairs of selector bitmasks and value masks. For example, for the
    bitmasks::

        A: 0001
        B: 0010
        C: 0100

    And the expression::

        A & (B | C)

    The build process happens as follows:


    1. We make an ExprCompiler for ``A``, with the selector and value mask
       both equal to ``0001``.
    2. We recurse into the second operand of the AND, ``(B | C)``, and:
        1. We make an ExprCompiler for ``B``, with the selector and value mask
           both equal to ``0010``.
        2. We make an ExprCompiler for ``C``, with the selector and value mask
           both equal to ``0100``.
        3. We OR the two ExprCompiler together, returning a new ExprCompiler
           with the two as separate clauses::

               ExprCompiler(clauses=[(0010, 0010), (0100, 0100)])
        4. We return the new ExprCompiler up to the caller
    3. We AND the ``A`` ExprCompiler with the ``(B | C)`` ExprCompiler, by
       ORing the bitmasks of each clause with ``A``::

           0010 | 0001 = 0011
           0100 | 0001 = 0101



           result = ExprCompiler(clauses=[(0011, 0011), (0101, 0101)])
    4. We compile that into a function of the form::

           clauses = [(0011, 0011), (0101, 0101)]
           def match(bitmask):
               return any(
                   bitmask & selector == valuemask
                   for selector, valuemask in clauses
               )
    """

    __slots__ = ("clauses",)

    def __init__(
        self, clauses: "Sequence[Tuple[_Selector, _ValueMask]]"
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

    def __and__(self, other: "ExprCompiler") -> "ExprCompiler":
        new_clauses = []
        for lselector, lvaluemask in self.clauses:
            for rselector, rvaluemask in other.clauses:
                common_selector = lselector & rselector
                if common_selector:
                    # if (x & ~x), drop the clause
                    if lvaluemask & common_selector != rvaluemask & rselector:
                        continue
                new_clauses.append(
                    ((lselector | rselector), (lvaluemask | rvaluemask))
                )
        return ExprCompiler(new_clauses)

    def __or__(self, other: "ExprCompiler") -> "ExprCompiler":
        return ExprCompiler([*self.clauses, *other.clauses])

    def _pretty_clauses(self) -> "List[str]":
        if not self.clauses:
            return []
        max_length = max(len(f"{clause[0]:b}") for clause in self.clauses)
        pretty_clauses = []
        for selector, valuemask in self.clauses:
            valuemask_str = f"{valuemask:b}".zfill(max_length)
            pretty_selector = f"{selector:b}".zfill(max_length).replace(
                "0", "."
            )
            pretty_clauses.append(
                "".join(
                    valuemask_str[i] if ch != "." else ch
                    for i, ch in enumerate(pretty_selector)
                )
            )
        return pretty_clauses

    def compile(
        self, expr_repr: "str" = "<unknown expression>"
    ) -> "CompiledFilter":
        clauses = self.clauses
        if not self.clauses:
            # FalseExpr
            def match(_: object, bitmask: "Bitmask") -> bool:
                return False

        elif len(self.clauses) == 1 and self.clauses[0][0] == 0:
            # TrueExpr
            def match(_: object, bitmask: "Bitmask") -> bool:
                return True

        elif len(self.clauses) == 1:
            # Fast path for single-clauses
            selector, valuemask = self.clauses[0]

            def match(_: object, bitmask: "Bitmask") -> bool:
                return bitmask & selector == valuemask

        else:

            def match(_: object, bitmask: "Bitmask") -> bool:
                return any(
                    bitmask & selector == valuemask
                    for selector, valuemask in clauses
                )

        class Filter(CompiledFilter):
            matches: "_CompiledMatcherType" = match  # type: ignore

        return Filter(expr_repr)


# Expression classes


class Expr(NonliteralTerm, ABC):
    """
    Base class for boolean expressions.
    """

    __slots__ = ()

    @abstractmethod
    def _make_compiler(self) -> "ExprCompiler":
        """
        Build an ExprCompiler out of this Expr's expression tree.
        """
        ...

    @abstractmethod
    def __invert__(self) -> "Term":
        ...

    @abstractmethod
    def __and__(self, other: "Term") -> "Term":
        ...

    @abstractmethod
    def __rand__(self, other: "Term") -> "Term":
        ...

    @abstractmethod
    def __or__(self, other: "Term") -> "Term":
        ...

    @abstractmethod
    def __ror__(self, other: "Term") -> "Term":
        ...

    @abstractmethod
    def matches(self, bitmask: "Bitmask") -> "bool":
        ...

    @abstractmethod
    def __str__(self) -> "str":
        ...

    def __repr__(self) -> "str":
        return f"{self.__class__}[{str(self)}]"


class StaticExpr(Expr, ABC):
    """
    Base class for expressions reducible to a form with no variables.
    """

    __slots__ = ()
    _retval: "bool" = False

    def __str__(self) -> "str":
        return str(self._retval).lower()

    def matches(self, bitmask: "Bitmask") -> "bool":
        return self._retval

    def __eq__(self, other: "object") -> "bool":
        if isinstance(other, self.__class__):
            return True
        return False

    def __hash__(self) -> "int":
        return hash(self.__class__)


class _TrueExpr(StaticExpr):
    """
    The simplified form of a expression that is always true, like A | ~A.

    Matches everything.
    """

    __slots__ = ()
    _retval = True

    def __invert__(self) -> "_FalseExpr":
        return FalseExpr

    def _make_compiler(self) -> "ExprCompiler":
        # Anything & 0 == 0
        return ExprCompiler(clauses=[(Bitmask(0), Bitmask(0))])

    def __or__(self, other: "Term") -> "_TrueExpr":
        return self

    __ror__ = __or__

    def __and__(self, other: "Term") -> "Term":
        return other

    __rand__ = __and__


class _FalseExpr(StaticExpr):
    """
    The simplified form of an unsatisfiable expression, like A & ~A.

    Matches nothing.
    """

    __slots__ = ()
    _retval = False

    def __invert__(self) -> "_TrueExpr":
        return TrueExpr

    def _make_compiler(self) -> "ExprCompiler":
        # any([]) == False
        return ExprCompiler(clauses=[])

    def __or__(self, other: "Term") -> "Term":
        return other

    __ror__ = __or__

    def __and__(self, other: "Term") -> "_FalseExpr":
        return self

    __rand__ = __and__


TrueExpr = _TrueExpr()
FalseExpr = _FalseExpr()


class DynExpr(Expr, ABC):
    """
    Base abstract class for "dynamic" filter expressions, that have arguments.

    Represents an unary expression, with a single operand.
    """

    __slots__ = ("matcher", "terms")
    _operator_repr: "ClassVar[str]" = "(Expr)"
    _matcher_combiner: "ClassVar[_MatcherCombinerType]" = and_

    @abstractmethod
    def _make_compiler(self) -> "ExprCompiler":
        ...

    def __init__(self, *terms: "Term"):
        self.terms: "Tuple[Term, ...]" = terms

    def __and__(self, other: "Term") -> "Term":
        if isinstance(other, AndExpr):
            return other.__rand__(self)
        return AndExpr(self, other)

    def __rand__(self, other: "Term") -> "Term":
        if isinstance(other, AndExpr):
            return other & self
        return AndExpr(other, self)

    def __or__(self, other: "Term") -> "Term":
        if isinstance(other, OrExpr):
            return other.__ror__(self)
        return OrExpr(self, other)

    def __ror__(self, other: "Term") -> "Term":
        if isinstance(other, OrExpr):
            return other | self
        return OrExpr(self, other)

    def __invert__(self) -> "Term":
        return NotExpr(self)

    def _make_compiler_for(self, term: "Term") -> "ExprCompiler":
        if isinstance(term, Expr):
            return self._extend_compiler(term._make_compiler())
        else:
            return self._get_component_compiler(term)

    def _get_component_compiler(self, term: "ComponentMeta") -> "ExprCompiler":
        return ExprCompiler(clauses=[(term._bitmask, term._bitmask)])

    def _extend_compiler(self, matcher: "ExprCompiler") -> "ExprCompiler":
        return matcher

    def __hash__(self) -> int:
        return hash((self.__class__, self.terms))

    def __eq__(self, other: "object") -> bool:
        return isinstance(other, self.__class__) and set(other.terms) == set(
            self.terms
        )


class NotExpr(DynExpr):
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

    def matches(self, bitmask: "Bitmask") -> "bool":
        return not matches(self.terms[0], bitmask)

    def _make_compiler(self) -> "ExprCompiler":
        return self._make_compiler_for(self.terms[0])

    def _get_component_compiler(self, term: "ComponentMeta") -> ExprCompiler:
        return ExprCompiler(clauses=[(term._bitmask, ZERO)])

    def _extend_compiler(self, matcher: "ExprCompiler") -> "NoReturn":
        raise TypeError("NotExpr._extend_matcher intentionally omitted.")

    def __invert__(self) -> "Term":
        return self.terms[0]

    def __or__(self, other: "Term") -> "Term":
        if other == ~self:
            return TrueExpr
        return super().__or__(other)

    def __ror__(self, other: "Term") -> "Term":
        if other == ~self:
            return TrueExpr
        return super().__or__(other)

    def __str__(self) -> "str":
        return f"~{_format_expr_term(self.terms[0])}"


class MultiExpr(DynExpr, ABC):
    """
    An abstract base class for 2+-ary expressions, like ``X & Y & Z``.
    """

    __slots__ = ()
    _operator_repr: "ClassVar[str]" = "(MultiExpr)"
    _matcher_combiner: "ClassVar[_MatcherCombinerType]" = and_

    def __str__(self) -> "str":
        return f"""{
            self._operator_repr.join(_format_expr_term(t) for t in self.terms)
            }"""

    def _make_compiler(self) -> "ExprCompiler":
        return reduce(
            # see: https://github.com/python/mypy/issues/5485
            self._matcher_combiner,  # type: ignore
            (self._make_compiler_for(term) for term in self.terms),
        )


class AndExpr(MultiExpr):
    """
    An "and" expression: ``X & Y``.

    Matches bitmasks matched by all of its operands.
    """

    __slots__ = ()
    _operator_repr = " & "

    def __and__(self, other: "Term") -> "Term":
        if isinstance(other, AndExpr):
            terms = (*self.terms, *other.terms)
            first = terms[0]
            if all(term == first for term in terms):
                return first
            return AndExpr(*terms)
        if other not in self.terms:
            return AndExpr(*self.terms, other)
        return self

    def __rand__(self, other: "Term") -> "Term":
        if isinstance(other, AndExpr):
            terms = (*other.terms, *self.terms)
            first = terms[0]
            if all(term == first for term in terms):
                return first
            return AndExpr(*other.terms, *self.terms)
        if other not in self.terms:
            return AndExpr(other, *self.terms)
        return self

    def __invert__(self) -> "OrExpr":
        # De Morgan's first law
        # ¬(A ∧ B) ⇔ ¬A ∨ ¬B
        return OrExpr(*map(inv, self.terms))

    def matches(self, bitmask: "Bitmask") -> "bool":
        return all(matches(term, bitmask) for term in self.terms)


class OrExpr(MultiExpr):
    """
    An "or" expression: ``X & Y``.

    Matches bitmasks matched by any of its operands.
    """

    __slots__ = ()
    _operator_repr = " | "
    _matcher_combiner: "ClassVar[_MatcherCombinerType]" = or_

    def __or__(self, other: "Term") -> "OrExpr":
        if isinstance(other, OrExpr):
            return OrExpr(
                *self.terms,
                *[term for term in other.terms if term not in self.terms],
            )
        elif other not in self.terms:
            return OrExpr(*self.terms, other)
        return self

    def __ror__(self, other: "Term") -> "OrExpr":
        if isinstance(other, AndExpr):
            return OrExpr(
                *[term for term in other.terms if term not in self.terms],
                *self.terms,
            )
        elif other not in self.terms:
            return OrExpr(other, *self.terms)
        return self

    def __invert__(self) -> "AndExpr":
        # De Morgan's second law
        # ¬(A ∨ B) ⇔ ¬A ∧ ¬B
        return AndExpr(*map(inv, self.terms))

    def matches(self, bitmask: "Bitmask") -> "bool":
        return any(matches(term, bitmask) for term in self.terms)
