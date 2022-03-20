from typing import Tuple, List

import pycosat
from pprint import pprint

from sat_utils import from_dnf, from_dnf_with_de_morgan


def assert_cnf_is_equivalent(cnf_1: List[Tuple[str]], cnf_2: List[Tuple[str]]):
    msg = f'\ncnf 1: {cnf_1}\ncnf 2: {cnf_2}'
    assert sorted([sorted(fact) for fact in cnf_1]) == sorted([sorted(fact) for fact in cnf_2]), msg


def play_with_from_dnf():
    # X = Y
    #   means
    # (~X | Y) & (~Y | X)
    groups = [('Y',)]
    expected_cnf_de_morgan = [('Y',)]
    assert_cnf_is_equivalent(expected_cnf_de_morgan, from_dnf_with_de_morgan(groups))
    expected_cnf_equisatisfiable = [('~0___', 'Y'), ('~Y', '0___'), ('0___',)]
    assert_cnf_is_equivalent(expected_cnf_equisatisfiable, from_dnf(groups))

    # X = A & B
    #   means
    # (X -> A & B) & (A & B -> X)
    #   means
    # (~X | A) & (~X | B) & (~A | ~B | X)
    groups = [('A', 'B')]
    expected_cnf_de_morgan = [('A',), ('B',)]
    assert_cnf_is_equivalent(expected_cnf_de_morgan, from_dnf_with_de_morgan(groups))
    expected_cnf_equisatisfiable = [('~1___', 'A'), ('~1___', 'B'), ('~A', '~B', '1___'), ('1___',)]
    assert_cnf_is_equivalent(expected_cnf_equisatisfiable, from_dnf(groups))

    groups = [('A', 'B', 'C'), ('D', 'E', 'F'), ('G', 'H', 'I')]
    expected_cnf_de_morgan = [
        ('A', 'D', 'G'), ('A', 'D', 'H'), ('A', 'D', 'I'), ('A', 'E', 'G'), ('A', 'E', 'H'), ('A', 'E', 'I'),
        ('A', 'F', 'G'), ('A', 'F', 'H'), ('A', 'F', 'I'), ('B', 'D', 'G'), ('B', 'D', 'H'), ('B', 'D', 'I'),
        ('B', 'E', 'G'), ('B', 'E', 'H'), ('B', 'E', 'I'), ('B', 'F', 'G'), ('B', 'F', 'H'), ('B', 'F', 'I'),
        ('C', 'D', 'G'), ('C', 'D', 'H'), ('C', 'D', 'I'), ('C', 'E', 'G'), ('C', 'E', 'H'), ('C', 'E', 'I'),
        ('C', 'F', 'G'), ('C', 'F', 'H'), ('C', 'F', 'I')
    ]
    assert_cnf_is_equivalent(expected_cnf_de_morgan, from_dnf_with_de_morgan(groups))
    expected_cnf_equisatisfiable = [('~2___', 'A'), ('~2___', 'B'), ('~2___', 'C'), ('~A', '~B', '~C', '2___'),
                                    ('~3___', 'D'), ('~3___', 'E'), ('~3___', 'F'), ('~D', '~E', '~F', '3___'),
                                    ('~4___', 'G'), ('~4___', 'H'), ('~4___', 'I'), ('~G', '~H', '~I', '4___'),
                                    ('2___', '3___', '4___')]
    assert_cnf_is_equivalent(expected_cnf_equisatisfiable, from_dnf(groups))

    groups = [tuple(f'{letter}{index}' for index in range(4)) for letter in 'ABCDE']
    assert len(from_dnf_with_de_morgan(groups)) == 4 ** 5
    assert len(from_dnf(groups)) == (4 + 1) * 5 + 1
    expected_cnf_equisatisfiable = [
        ('~10___', 'A0'), ('~10___', 'A1'), ('~10___', 'A2'), ('~10___', 'A3'), ('~A0', '~A1', '~A2', '~A3', '10___'),
        ('~11___', 'B0'), ('~11___', 'B1'), ('~11___', 'B2'), ('~11___', 'B3'), ('~B0', '~B1', '~B2', '~B3', '11___'),
        ('~12___', 'C0'), ('~12___', 'C1'), ('~12___', 'C2'), ('~12___', 'C3'), ('~C0', '~C1', '~C2', '~C3', '12___'),
        ('~13___', 'D0'), ('~13___', 'D1'), ('~13___', 'D2'), ('~13___', 'D3'), ('~D0', '~D1', '~D2', '~D3', '13___'),
        ('~14___', 'E0'), ('~14___', 'E1'), ('~14___', 'E2'), ('~14___', 'E3'), ('~E0', '~E1', '~E2', '~E3', '14___'),
        ('10___', '11___', '12___', '13___', '14___')]
    assert_cnf_is_equivalent(expected_cnf_equisatisfiable, from_dnf(groups))


if __name__ == '__main__':
    # pprint(list(pycosat.itersolve([(-1, 2), (-1, 3)])), width=20)
    play_with_from_dnf()
