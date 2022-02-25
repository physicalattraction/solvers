import pycosat
from pprint import pprint

if __name__ == '__main__':
    pprint(list(pycosat.itersolve([(-1, 2), (-1, 3)])), width=20)
