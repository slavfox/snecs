from typing import TYPE_CHECKING, Union, cast
from abc import ABC, abstractmethod
from functools import partial, reduce
from itertools import combinations_with_replacement
from operator import and_, not_, or_

from snecs._detail import Bitmask
from snecs._detail import bits as bitmask_bits

if TYPE_CHECKING:
    from typing import Callable, Set
    from snecs.component import ComponentMeta


Term = Union["Expr", "ComponentMeta"]


def _match_single_term(
    term: "Term", entity_mask: "Bitmask", matcher: "Callable[[int], bool]"
) -> "bool":
    if isinstance(term, Expr):
        return matcher(term.match(entity_mask))
    return matcher(term._bitmask & entity_mask)


def dumpquery(expr: "Term") -> "str":
    if isinstance(expr, Expr):
        return expr._pretty_print()
    else:
        return expr.__name__


class Expr(ABC):
    __slots__ = ("right",)
    _pretty_operator: "str" = ""

    def __init__(self, right: "Term") -> "None":
        self.right: "Term" = right

    @property
    def _bitmask(self) -> "Bitmask":
        return self.right._bitmask

    def __and__(self, other: "Term") -> "AndExpr":
        return AndExpr(other, self)

    def __or__(self, other: "Term") -> "OrExpr":
        return OrExpr(other, self)

    def __invert__(self) -> "NotExpr":
        return NotExpr(self)

    def _pretty_print(self) -> "str":
        return f"({self._pretty_operator} {dumpquery(self.right)})"

    @abstractmethod
    def match(self, bitmask: "Bitmask") -> "bool":
        ...


class NotExpr(Expr):
    _pretty_operator = "not"

    def match(self, bitmask: "Bitmask") -> "bool":
        return _match_single_term(self.right, bitmask, not_)


class BinExpr(Expr, ABC):
    __slots__ = ("left",)

    @property
    @abstractmethod
    def _pretty_operator(self) -> "str":  # type: ignore
        pass

    @property
    def _bitmask(self) -> "Bitmask":
        return self.right._bitmask | self.left._bitmask

    def __init__(self, left: "Term", right: "Term") -> "None":
        super().__init__(right)
        self.left: "Term" = left

    def __and__(self, other: "Term") -> "AndExpr":
        return AndExpr(other, self)

    def __or__(self, other: "Term") -> "OrExpr":
        return OrExpr(other, self)

    def __invert__(self) -> "NotExpr":
        return NotExpr(self)

    def _pretty_print(self) -> "str":
        return (
            f"({self._pretty_operator} "
            f"{dumpquery(self.left)} "
            f"{dumpquery(self.right)})"
        )


class AndExpr(BinExpr):
    _pretty_operator: "str" = "and"

    def match(self, bitmask: "Bitmask") -> "bool":
        left_match = _match_single_term(self.left, bitmask, bool)
        right_match = _match_single_term(self.right, bitmask, bool)
        return left_match and right_match


class OrExpr(BinExpr):
    _pretty_operator: "str" = "or"

    def match(self, bitmask: "Bitmask") -> "bool":
        left_match = _match_single_term(self.left, bitmask, bool)
        right_match = _match_single_term(self.right, bitmask, bool)
        return left_match or right_match


def compile_filter(expr: "Term") -> "Callable[[Bitmask], bool]":
    """
    Compile a filter expression into a much faster form.
    """
    if not isinstance(expr, Expr):
        # PyCharm has a false positive here
        # noinspection PyTypeChecker
        return partial(and_, expr._bitmask)
    # Bitmask with all the bits that influence the output at all set to 1
    expmask = expr._bitmask
    # List of the individual bits. Eg. for a bitmask 0100 1011, this will be:
    # [1, 2, 8, 64]
    expbits = list(bitmask_bits(expmask))
    mask_width = len(expbits)
    valid_values: "Set[Bitmask]" = set()
    # generate all combinations of ones and zeroes of length `mask_width`
    for bits in combinations_with_replacement((1, 0), mask_width):
        # Map bits to bitmask. This is very simple, but non-obvious, so here
        # I go trying to explain this to future-me again. Let's take our
        # earlier example.
        #
        #     expmask == 0b_0100_1011
        #     expbits == [1, 2, 8, 64]
        #     mask_width == len(expbits) == 4
        #
        # combinations_with_replacement() will give us an iterator over all
        # the 4-length combinations of ones and zeroes. We get a list like:
        #              x  x  v  v
        #     bits == [0, 0, 1, 1]
        #
        # We map every i-th bit in `bits` to the i-th bit in `expbits`,
        # by multiplying them:
        #
        #     expbits[i] * bit for i, bit in ...
        #
        # This gives us [0, 0, 8, 64], which we then foldl by or_-ing the
        # bits together, giving us back a bitmask:
        #         v   v xx
        #     0b_0100_1000
        #
        # I'd hate to be using a `cast`, normally, but this is off the hot
        # path.
        bitmask: "Bitmask" = cast(
            Bitmask,
            reduce(or_, (expbits[i] * bit for i, bit in (enumerate(bits)))),
        )
        # If the resulting bitmask matches the filter expression,
        # it is added to the set of valid values.
        if expr.match(bitmask):
            valid_values.add(bitmask)

    def match(entity_bitmask: "Bitmask") -> "bool":
        return (expmask & entity_bitmask) in valid_values

    return match
