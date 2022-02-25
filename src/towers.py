import string

import itertools
from sys import intern
from typing import Collection, Dict, List

from sat_utils import basic_fact, from_dnf, one_of, solve_one

Point = str


def comb(point: Point, value: int) -> str:
    """
    Format a fact (a value assigned to a given point), and store it into the interned strings table

    :param point: Point on the grid, characterized by two letters, e.g. AB
    :param value: Value of the cell on that point, e.g. 2
    :return: Fact string 'AB 2'
    """

    return intern(f'{point} {value}')


def visible_from_line(line: Collection[int], reverse: bool = False) -> int:
    """
    Return how many towers are visible from the given line

    >>> visible_from_line([1, 2, 3, 4])
    4
    >>> visible_from_line([1, 4, 3, 2])
    2
    """

    visible = 0
    highest_seen = 0
    for number in reversed(line) if reverse else line:
        if number > highest_seen:
            visible += 1
            highest_seen = number
    return visible


class TowersPuzzle:
    def __init__(self):
        self.visible_from_top = [3, 3, 2, 1]
        self.visible_from_bottom = [1, 2, 3, 2]
        self.visible_from_left = [3, 3, 2, 1]
        self.visible_from_right = [1, 2, 3, 2]
        self.given_numbers = {'AC': 3}

        # self.visible_from_top = [3, 2, 1, 4, 2]
        # self.visible_from_bottom = [2, 2, 4, 1, 2]
        # self.visible_from_left = [3, 2, 3, 1, 3]
        # self.visible_from_right = [2, 2, 1, 3, 2]

        self._cnf = None
        self._solution = None

    def display_puzzle(self):
        print('*** Puzzle ***')
        self._display(self.given_numbers)

    def display_solution(self):
        print('*** Solution ***')
        point_to_value = {point: value for point, value in [fact.split() for fact in self.solution]}
        self._display(point_to_value)

    @property
    def n(self) -> int:
        """
        :return: Size of the grid
        """

        return len(self.visible_from_top)

    @property
    def points(self) -> List[Point]:
        return [''.join(letters) for letters in itertools.product(string.ascii_uppercase[:self.n], repeat=2)]

    @property
    def rows(self) -> List[List[Point]]:
        """
        :return: Points, grouped per row
        """

        return [self.points[i:i + self.n] for i in range(0, self.n * self.n, self.n)]

    @property
    def cols(self) -> List[List[Point]]:
        """
        :return: Points, grouped per column
        """

        return [self.points[i::self.n] for i in range(self.n)]

    @property
    def values(self) -> List[int]:
        return list(range(1, self.n + 1))

    @property
    def cnf(self):
        if self._cnf is None:
            cnf = []

            # Each point assigned exactly one value
            for point in self.points:
                cnf += one_of(comb(point, value) for value in self.values)

            # Each value gets assigned to exactly one point in each row
            for row in self.rows:
                for value in self.values:
                    cnf += one_of(comb(point, value) for point in row)

            # Each value gets assigned to exactly one point in each col
            for col in self.cols:
                for value in self.values:
                    cnf += one_of(comb(point, value) for point in col)

            # Set visible from left
            if self.visible_from_left:
                for index, row in enumerate(self.rows):
                    target_visible = self.visible_from_left[index]
                    if not target_visible:
                        continue
                    possible_perms = []
                    for perm in itertools.permutations(range(1, self.n + 1)):
                        if visible_from_line(perm) == target_visible:
                            possible_perms.append(tuple(
                                comb(point, value)
                                for point, value in zip(row, perm)
                            ))
                    cnf += from_dnf(possible_perms)

            # Set visible from right
            if self.visible_from_right:
                for index, row in enumerate(self.rows):
                    target_visible = self.visible_from_right[index]
                    if not target_visible:
                        continue
                    possible_perms = []
                    for perm in itertools.permutations(range(1, self.n + 1)):
                        if visible_from_line(perm, reverse=True) == target_visible:
                            possible_perms.append(tuple(
                                comb(point, value)
                                for point, value in zip(row, perm)
                            ))
                    cnf += from_dnf(possible_perms)

            # Set visible from top
            if self.visible_from_top:
                for index, col in enumerate(self.cols):
                    target_visible = self.visible_from_top[index]
                    if not target_visible:
                        continue
                    possible_perms = []
                    for perm in itertools.permutations(range(1, self.n + 1)):
                        if visible_from_line(perm) == target_visible:
                            possible_perms.append(tuple(
                                comb(point, value)
                                for point, value in zip(col, perm)
                            ))
                    cnf += from_dnf(possible_perms)

            # Set visible from bottom
            if self.visible_from_bottom:
                for index, col in enumerate(self.cols):
                    target_visible = self.visible_from_bottom[index]
                    if not target_visible:
                        continue
                    possible_perms = []
                    for perm in itertools.permutations(range(1, self.n + 1)):
                        if visible_from_line(perm, reverse=True) == target_visible:
                            possible_perms.append(tuple(
                                comb(point, value)
                                for point, value in zip(col, perm)
                            ))
                    cnf += from_dnf(possible_perms)

            # Set given numbers
            for point, value in self.given_numbers.items():
                cnf += basic_fact(comb(point, value))

            self._cnf = cnf

        return self._cnf

    @property
    def solution(self):
        if self._solution is None:
            self._solution = solve_one(self.cnf)
        return self._solution

    def _display(self, facts: Dict[Point, int]):
        top_line = '    ' + ' '.join([str(elem) if elem else ' ' for elem in self.visible_from_top]) + '    '
        print(top_line)
        print('-' * len(top_line))
        for index, row in enumerate(self.rows):
            elems = [str(self.visible_from_left[index]) or ' ', '|'] + \
                    [str(facts.get(point, ' ')) for point in row] + \
                    ['|', str(self.visible_from_right[index]) or ' ']
            print(' '.join(elems))
        print('-' * len(top_line))
        bottom_line = '    ' + ' '.join([str(elem) if elem else ' ' for elem in self.visible_from_bottom]) + '    '
        print(bottom_line)
        print()


if __name__ == '__main__':
    puzzle = TowersPuzzle()
    puzzle.display_puzzle()
    puzzle.display_solution()
