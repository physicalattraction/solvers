"""
https://rhettinger.github.io/einstein.html#sudoku-puzzles
"""
from typing import List

from sys import intern

from sat_utils import basic_fact, one_of, solve_one

n = 3

grid = '''\
AA AB AC BA BB BC CA CB CC
AD AE AF BD BE BF CD CE CF
AG AH AI BG BH BI CG CH CI
DA DB DC EA EB EC FA FB FC
DD DE DF ED EE EF FD FE FF
DG DH DI EG EH EI FG FH FI
GA GB GC HA HB HC IA IB IC
GD GE GF HD HE HF ID IE IF
GG GH GI HG HH HI IG IH II
'''

values = list('123456789')

table = [row.split() for row in grid.splitlines()]
points = grid.split()
subsquares = dict()
for pt in points:
    subsquares.setdefault(pt[0], []).append(pt)
# Groups:  rows   + columns           + subsquares
# The groups represent the grouped cells that must contain a 1 through 9
groups = table[:] + list(zip(*table)) + list(subsquares.values())
print(groups)
del grid, subsquares, table  # analysis requires only:  points, values, groups


def comb(point: str, value: int) -> str:
    """
    Format a fact (a value assigned to a given point), and store it into the interned strings table

    :param point: Point on the grid, characterized by two letters, e.g. AB
    :param value: Value of the cell on that point, e.g. 2
    :return: Fact string 'AB 2'
    """

    return intern(f'{point} {value}')


def str_to_facts(s) -> List[str]:
    """
    Convert str in row major form to a list of facts

    :param s: Sudoku string representation
    53  7    6  195    98    6 8   6   34  8 3  17   2   6 6    28    419  5    8  79
    :return: Sudoku list of facts representation
    ['AA 5', 'AB 3', 'BB 7', 'AD 6', 'BD 1', 'BE 9', 'BF 5', 'AH 9', 'AI 8', 'CH 6',
    'DA 8', 'EB 6', 'FC 3', 'DD 4', 'ED 8', 'EF 3', 'FF 1', 'DG 7', 'EH 2', 'FI 6',
    'GB 6', 'IA 2', 'IB 8', 'HD 4', 'HE 1', 'HF 9', 'IF 5', 'HH 8', 'IH 7', 'II 9']
    """

    return [comb(point, value) for point, value in zip(points, s) if
            value != ' ']


def facts_to_str(facts: List[str]) -> str:
    """
    Convert a list of facts to a string in row major order with blanks for unknowns

    :param facts: Sudoku list of facts representation
    :return: Sudoku string representation
    """

    point_to_value = dict(map(str.split, facts))
    return ''.join(point_to_value.get(point, ' ') for point in points)


def show(flatline):
    """
    Display grid from a string (values in row major order with blanks for unknowns)

    :param flatline: Sudoku string representation
    """

    fmt = '|'.join(['%s' * n] * n)
    sep = '+'.join(['-' * n] * n)
    for i in range(n):
        for j in range(n):
            offset = (i * n + j) * n ** 2
            print(fmt % tuple(flatline[offset:offset + n ** 2]))
        if i != n - 1:
            print(sep)


def solve(puzzle):
    """
    Solve the given puzzle

    :param puzzle: Sudoku string representation
    """

    cnf = []

    # each point assigned exactly one value
    for point in points:
        cnf += one_of(comb(point, value) for value in values)

    # each value gets assigned to exactly one point in each group
    for group in groups:
        for value in values:
            cnf += one_of(comb(point, value) for point in group)

    # add facts for known values in a specific puzzle
    for known in str_to_facts(puzzle):
        cnf += basic_fact(known)

    # solve it and display the results
    result = facts_to_str(solve_one(cnf))
    show(puzzle)
    print()
    show(result)
    print('=-' * 20)


if __name__ == '__main__':
    puzzles = [
        '53  7    6  195    98    6 8   6   34  8 3  17   2   6 6    28    419  5    8  79',
        '       75  4  5   8 17 6   36  2 7 1   5 1   1 5 8  96   1 82 3   4  9  48       ',
        ' 9 7 4  1    6 2 8    1 43  6     59   1 3   97     8  52 7    6 8 4    7  5 8 2 ',
        '67 38      921   85    736 1 8  4 7  5 1 8 4  2 6  8 5 175    24   321      61 84',
        '27  15  8   3  7 4    7     5 1   7   9   2   6   2 5     8    6 5  4   8  59  41',
        '8 64 3    5     7     2    32  8  5   8 5 4  1   7  93    4     9     4    6 72 8',
    ]
    for given in puzzles:
        solve(given)
