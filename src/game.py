from typing import List, Dict, TypeVar

class InvalidResourceException(Exception):
    """Custom error handler for creation of unidentified resource"""

class Resource:
    def __init__(self, name: str):
        if name in ("Brick", "Lumber", "Ore", "Grain", "Wool"):
            self.name = name
        else:
            raise InvalidResourceException(f"{name} is not a resource")

    def __repr__(self):
        return self.name

class Tile:
    """A single tile on the Catan game board"""

    Self = TypeVar("Self", bound="Tile")
    
    resource_dict: Dict[str, Resource | None] = {
        "Desert": None,
        "Hills": Resource("Brick"),
        "Forest": Resource("Lumber"),
        "Mountains": Resource("Ore"),
        "Fields": Resource("Grain"),
        "Pasture": Resource("Wool")
    }

    def __init__(self, terrain: str, number: int, neighbours: List[Self]):
        self.terrain = terrain
        self.number = number
        self.neighbours = neighbours
        self.resource = self.resource_dict[self.terrain]
        self.construction_slots: List[Construction]
        self.road_slots: List[Road]

    def check_proc(self, number: int):
        if self.number == number:
            return self.resource_dict[self.terrain]
        return None

class Construction:
    """An item constructed by a player"""
    pass

class Road:
    """A road placed by a player"""

# x = Resource("hi")