from enum import Enum, auto
from typing import List, Dict, TypeVar

class Resource(Enum):
    """Used by players to build construction items"""
    Brick = auto()
    Lumber = auto()
    Ore = auto()
    Grain = auto()
    Wool = auto()

class Tile:
    """A single tile on the Catan game board"""

    Self = TypeVar("Self", bound="Tile")
    
    resource_dict: Dict[str, str | None] = {
        "Desert": None,
        "Hills": Resource.Brick,
        "Forest": Resource.Lumber,
        "Mountains": Resource.Ore,
        "Fields": Resource.Grain,
        "Pasture": Resource.Wool
    }

    def __init__(self, terrain: str, number: int, neighbours: List[Self]):
        self.terrain = terrain
        self.number = number
        self.neighbours = neighbours
        self.resource = self.resource_dict[self.terrain]
        self.construction_slots: List[Construction]
        self.road_slots: List[Construction]

    def check_proc(self, number: int):
        return self.resource if number == self.number else None

class Construction:
    """An item constructed by a player"""

    construction_dict = {
        "Road": [
            Resource.Brick,
            Resource.Lumber
        ],
        "Settlement": [
            Resource.Brick,
            Resource.Lumber,
            Resource.Wool,
            Resource.Grain
        ],
        "City": [
            Resource.Ore,
            Resource.Ore,
            Resource.Ore,
            Resource.Grain,
            Resource.Grain
        ],
        "Development Card": [
            Resource.Ore,
            Resource.Wool,
            Resource.Grain
        ]
    }

    def __init__(self, name: str):
        assert name in self.construction_dict.keys()
        self.name = name
