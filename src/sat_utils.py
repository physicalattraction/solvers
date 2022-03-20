"""
Utility functions to humanize interaction with pycosat
"""

from functools import lru_cache
from itertools import combinations
from sys import intern
from typing import List, Tuple, Collection

import pycosat  # https://pypi.python.org/pypi/pycosat

Fact = str
Dnf = List[Tuple[Fact]]
Cnf = List[Tuple[Fact]]

# Uses pseudo-namespacing to avoid collisions.
_EXT_SUFFIX = "___"
_NEXT_EXT_INDEX = 0


def is_ext_var(element: Fact) -> bool:
    return element.endswith(_EXT_SUFFIX)


def ext_var() -> Fact:
    global _NEXT_EXT_INDEX
    ext_index = _NEXT_EXT_INDEX
    _NEXT_EXT_INDEX += 1

    return intern(f'{ext_index}{_EXT_SUFFIX}')


def make_translate(cnf: Cnf):
    """
    Make translator from symbolic CNF to PycoSat's numbered clauses

    Return a literal to number dictionary and reverse lookup dict

    >>> make_translate([('~a', 'b', '~c'), ('a', '~c')])
    ({'a': 1, '~a': -1, 'b': 2, '~b': -2, 'c': 3, '~c': -3},
     {1: 'a', -1: '~a', 2: 'b', -2: '~b', 3: 'c', -3: '~c'})
    """

    lit2num = {}
    for clause in cnf:
        for literal in clause:
            if literal not in lit2num:
                var = literal[1:] if literal[0] == '~' else literal
                num = len(lit2num) // 2 + 1
                lit2num[intern(var)] = num
                lit2num[intern('~' + var)] = -num
    num2var = {num: lit for lit, num in lit2num.items()}
    return lit2num, num2var


def translate(cnf: Cnf, uniquify=False):
    """
    Translate a symbolic cnf to a numbered cnf and return a reverse mapping

    :param cnf:
    :param uniquify:
    :return:
    """

    # DIMACS CNF file format:
    # http://people.sc.fsu.edu/~jburkardt/data/cnf/cnf.html
    if uniquify:
        cnf = list(dict.fromkeys(cnf))
    lit2num, num2var = make_translate(cnf)
    numbered_cnf = [tuple([lit2num[lit] for lit in clause]) for clause in cnf]
    return numbered_cnf, num2var


def itersolve(symbolic_cnf: Cnf, include_neg=False):
    numbered_cnf, num2var = translate(symbolic_cnf)
    for solution in pycosat.itersolve(numbered_cnf):
        yield [num2var[n] for n in solution if include_neg or n > 0]


def solve_all(symcnf: Cnf, include_neg=False):
    return list(itersolve(symcnf, include_neg))


def solve_one(symcnf: Cnf, include_neg=False):
    return next(itersolve(symcnf, include_neg))


############### Support for Building CNFs ##########################

@lru_cache(maxsize=None)
def neg(element: Fact) -> Fact:
    """
    Negate a single element

    >>> neg('A')
    '~A'
    >>> neg('~A')
    'A'
    """

    return intern(element[1:] if element.startswith('~') else '~' + element)


def from_dnf_with_de_morgan(groups: Dnf) -> Cnf:
    """
    Convert from or-of-ands to and-of-ors

    :param groups: A list of tuples, where each tuple is an AND, and the list is an OR
                   [('A', 'B', 'C'), ('D', 'E', 'F'), ('G', 'H', 'I')]
                        means
                   (A and B and C) or (D and E and F) or (G and H and I)
    :return: A list of tuples, where each tuple is an OR, and the list is an AND
             [ ('A', 'D', 'G'), ('A', 'D', 'H'), ..., ('C', 'F', 'H'), ('C', 'F', 'I') ]
                 means
             (A or D or G) and (A or D or H) and ... and (C or F or H) and (C or F or I)
    """

    cnf = {frozenset()}
    for group_index, group in enumerate(groups, start=1):
        nl = {frozenset([literal]): neg(literal) for literal in group}
        # The "clause | literal" prevents dup lits: {x, x, y} -> {x, y}
        # The nl check skips over identities: {x, ~x, y} -> True
        cnf = {clause | literal for literal in nl for clause in cnf
               if nl[literal] not in clause}
        # The sc check removes clauses with superfluous terms:
        #     {{x}, {x, z}, {y, z}} -> {{x}, {y, z}}
        # Should this be left until the end?
        sc = min(cnf, key=len)  # XXX not deterministic
        cnf -= {clause for clause in cnf if clause > sc}
    return list(map(tuple, cnf))


def from_dnf(groups) -> Cnf:
    """
    Convert from or-of-ands to and-of-ors, equisatisfiably

    Equisatisfiabily means that we add extension variables in such a way that the input is true
    if and only if the output is true. However, they are not equivalent. We are using the
    Tseytin transformation to do so. https://en.wikipedia.org/wiki/Tseytin_transformation
    The implementation comes from https://stackoverflow.com/a/71542523/1469465

    >>> from_dnf(groups=[('A', 'B', 'C'), ('D', 'E', 'F'), ('G', 'H', 'I')])
    [('~0___', 'A'), ('~0___', 'B'), ('~0___', 'C'), ('~A', '~B', '~C', '0___'), ('~1___', 'D'), ('~1___', 'E'), ('~1___', 'F'), ('~D', '~E', '~F', '1___'), ('~2___', 'G'), ('~2___', 'H'), ('~2___', 'I'), ('~G', '~H', '~I', '2___'), ('0___', '1___', '2___')]

    :param groups: A list of tuples, where each tuple is an OR, and the list is an AND
                   [('A', 'B', 'C'), ('D', 'E', 'F'), ('G', 'H', 'I')]
                        means
                   (A and B and C) or (D and E and F) or (G and H and I)
    :return: A list of tuples, where each tuple is an AND, and the list is an OR
             [('~0___', 'A'), ('~0___', 'B'), ('~0___', 'C'), ('~A', '~B', '~C', '0___'), ..., ('0___', '1___', '2___')]
                 means
             (~0 or A) and (~0 or B) and (~0 or C) and ... and (0 or 1 or 2)
                 where
             0 = (A and B and C), 1 = (D and E and F), 2 = (G and H and I)
    """

    cnf = []

    extension_vars = []
    for group in groups:
        extension_var = ext_var()
        neg_extension_var = neg(extension_var)

        imply_ext_clause = []
        for literal in group:
            imply_ext_clause.append(neg(literal))
            cnf.append((neg_extension_var, literal))  # ('~0___', 'A')
        imply_ext_clause.append(extension_var)
        cnf.append(tuple(imply_ext_clause))  # ('~A', '~B', '~C', '0___')
        extension_vars.append(extension_var)

    cnf.append(tuple(extension_vars))  # ('0___', '1___', '2___')
    return cnf


class Q:
    """
    Quantifier for the number of elements that are true
    """

    def __init__(self, elements: Collection[Fact]):
        self.elements = tuple(elements)

    def __lt__(self, n: int) -> Cnf:
        """
        >>> q = Q(['A', 'B'])
        >>> q < 1
        [('~A',), ('~B',)]
        >>> q < 5
        []

        :param n: The number of statements that are true are less than this number
        :return: Conjunctive normal form of facts such that the above statement holds
        """

        return list(combinations(map(neg, self.elements), n))

    def __le__(self, n: int) -> Cnf:
        return self < n + 1

    def __gt__(self, n: int) -> Cnf:
        """
        >>> q = Q(['A', 'B'])
        >>> q > 1
        [('A',), ('B',)]
        >>> q > -1
        []

        :param n: The number of statements that are true are greater than this number
        :return: Conjunctive normal form of facts such that the above statement holds
        """

        return list(combinations(self.elements, len(self.elements) - n))

    def __ge__(self, n: int) -> Cnf:
        return self > n - 1

    def __eq__(self, n: int) -> Cnf:
        return (self <= n) + (self >= n)

    def __ne__(self, n) -> Cnf:
        raise NotImplementedError

    def __repr__(self) -> str:
        """
        >>> Q(['A', 'B'])
        Q(elements=('A', 'B'))
        """

        return f'{self.__class__.__name__}(elements={self.elements!r})'


def all_of(elements: List[Fact]) -> Cnf:
    """
    Forces inclusion of matching rows on a truth table
    """

    return Q(elements) == len(elements)


def some_of(elements: List[Fact]) -> Cnf:
    """
    At least one of the elements must be true
    """

    return Q(elements) >= 1


def one_of(elements: List[Fact]) -> Cnf:
    """
    Exactly one of the elements is true
    """

    return Q(elements) == 1


def basic_fact(element: Fact) -> Cnf:
    """
    Assert that this one element always matches
    """

    return Q([element]) == 1


def none_of(elements) -> Cnf:
    """
    Forces exclusion of matching rows on a truth table
    """

    return Q(elements) == 0
