from typing import List, Dict, TypeVar

class InvalidResourceException(Exception):
    """Custom error handler for creation of unidentified resource"""

class Tile:
    """A single tile on the Catan game board"""

    Self = TypeVar("Self", bound="Tile")
    
    resource_dict: Dict[str, str | None] = {
        "Desert": None,
        "Hills": "Brick",
        "Forest": "Lumber",
        "Mountains": "Ore",
        "Fields": "Grain",
        "Pasture": "Wool"
    }

    def __init__(self, terrain: str, number: int, neighbours: List[Self]):
        self.terrain = terrain
        self.number = number
        self.neighbours = neighbours
        self.resource = self.resource_dict[self.terrain]
        self.construction_slots: List[Construction]
        self.road_slots: List[Construction]

    def check_proc(self, number: int):
        if self.number == number:
            return self.resource
        return None

class Construction:
    """An item constructed by a player"""

    # construction_dict = {
    #     "Road": [
    #         Tile.resource_dict 
    #     ]
    # }

    # def __init__(self, name: str):
    #     if name in ("Road", "Settlement")
