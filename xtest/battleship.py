#!/usr/bin/env python3

import logging

from dataclasses import dataclass
from enum import Enum
from typing import List

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

@dataclass
class Ship:
  length: int
  name: str
  symbol: str

class Ship(Enum):
  no  = Ship(1, "Miss", "・")
  destroyer = Ship(2, "Destroyer", "d")
  submarine = Ship(3, "Submarine", "s")
  cruiser = Ship(3, "Cruiser", "c")
  battleship = Ship(4, "Battleship", "b")
  carrier = Ship(5, "Carrier", "a")


@dataclass
class Point:
    row: str
    col: int
    viewed: bool
    ship: Ship


class Board:
  ocean: List[List[Point]]

  def __init__(self):
    self.ocean = [[Point(row, col, False, Ship.no)for col in range(1, 11)] for row in 'ABCDEFGHIJ']

  def show(self):
    grid = ''
    for row in ocean:
      for tile in row:
        if tile.viewed:
          grid += tile.ship.symbol
        else:
          grid += ' '
      grid += '\n'
    return grid


def main():
