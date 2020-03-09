from abc import ABC, abstractmethod

from snecs._detail import Bitmask

from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from typing import Type
    from snecs.component import ComponentMeta, Component


Term = Union["Expr", "ComponentMeta"]


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

    def __and__(self, other: "Term") -> "AndExpr":
        return AndExpr(other, self)

    def __or__(self, other: "Term") -> "OrExpr":
        return OrExpr(other, self)

    def __invert__(self) -> "NotExpr":
        return NotExpr(self)

    def _pretty_print(self) -> "str":
        return f"({self._pretty_operator} {dumpquery(self.right)})"

    def compile(self) -> "Filter":
        if isinstance(self.right, Expr):
            return self.right.compile()
        else:
            return Filter(self.right._bitmask)


class NotExpr(Expr):
    _pretty_operator = "not"

    def compile(self) -> "Filter":
        if isinstance(self.right, Expr):
            return self.right.compile()  # this is wrong


class BinExpr(Expr, ABC):
    __slots__ = ("left",)

    @property
    @abstractmethod
    def _pretty_operator(self) -> "str":  # type: ignore
        pass

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


class OrExpr(BinExpr):
    _pretty_operator: "str" = "or"


class Filter:
    __slots__ = ("bitmask",)

    def __init__(self, bitmask: "Bitmask", clauses=()) -> "None":
        self.bitmask: "Bitmask" = bitmask

    def match(self, bitmask: "Bitmask"):
        pass
