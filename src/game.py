"""This file contains all game logic components as a library"""
from enum import Enum, auto
from typing import List, Set, Dict, TypeVar

class Resource(Enum):
    """Used by players to build construction items"""
    Brick = auto()
    Lumber = auto()
    Ore = auto()
    Grain = auto()
    Wool = auto()

class Player:
    """A player of the game of Catan"""

    def __init__(self, name="Default"):
        self.name = name
        self.resources: List[Resource] = []
        self.development_cards: List[DevelopmentCard] = []
        self.occupied_tiles: Set[Tile] = set()
        self.victory_points = 0

    @property
    def controlled_tiles(self):
        return [tile for tile in self.occupied_tiles if any(c is not None and c.owner is self for c in tile.construction_slots)]

    @property
    def constructions(self):
        return [item for tile in self.controlled_tiles for item in tile.construction_slots 
            if item is not None and item.owner is self]

    @property
    def roads(self):
        return [item for tile in self.occupied_tiles for item in tile.road_slots 
            if item is not None and item.owner is self]

    def __repr__(self):
        return self.name

    def build(self, item):
        assert Construction.can_build(self, item)

class Harbour:
    """A trading port that can be used for better deals"""
    pass

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

    def __init__(self, terrain: str, number: int, neighbours: List[Self | None]=[None for _ in range(6)], harbour=None):
        self.terrain = terrain
        self.number = number
        assert len(neighbours) <= 6
        self.neighbours = neighbours
        self.resource = self.resource_dict[self.terrain]
        self.construction_slots: List[Construction | None] = [None for _ in range(6)]
        self.road_slots: List[Road | None] = [None for _ in range(6)]
        self.harbour_slot: Harbour | None = harbour

    def edge_neighbours(self, edge_idx: int):
        """Determine, given a single edge on the tile, what other tiles intersect with the edge"""
        if edge_idx == 0:
            return [n for n in self.neighbours[6:0:-4] if n is not None]
        return [n for n in self.neighbours[edge_idx-1:edge_idx+1] if n is not None]


    def check_proc(self, number: int):
        return self.resource if number == self.number else None

class Construction:
    """An item constructed by a player"""

    construction_dict = {
        "Road": {
            Resource.Brick: 1,
            Resource.Lumber: 1
        },
        "Settlement": {
            Resource.Brick: 1,
            Resource.Lumber: 1,
            Resource.Wool: 1,
            Resource.Grain: 1
        },
        "City": {
            Resource.Ore: 3,
            Resource.Grain: 2
        },
        "Development Card": {
            Resource.Ore: 1,
            Resource.Wool: 1,
            Resource.Grain: 1
        }
    }

    @staticmethod
    def can_build(player: Player, item: str):
        return all(player.resources.count(key) >= val for key, val in Construction.construction_dict[item].items())

    def __init__(self, name: str, owner: Player):
        assert name in self.construction_dict.keys()
        self.name = name
        self.owner = owner

    def __repr__(self):
        return f"{self.owner}'s {self.name}"

class Road(Construction):
    """A road to put your wagon on"""

    def __init__(self, owner: Player, tile: Tile, slot_idx: int):
        assert 0 <= slot_idx < 6 and tile.road_slots[slot_idx] is None
        self.tile = tile
        self.tile.road_slots[slot_idx] = self
        super().__init__("Road", owner)
        self.owner.occupied_tiles.add(tile)

class SettlementOrCity(Construction):
    """Hybrid class for settlements/cities"""

    def __init__(self, owner: Player, tile: Tile, slot_idx: int):
        assert 0 <= slot_idx < 6 and tile.construction_slots[slot_idx] is None
        self.tiles = [tile] + tile.edge_neighbours(slot_idx)
        for e, tile in enumerate(self.tiles):
            idx = slot_idx + ((e * 2) % 6) # edges are returned clockwise; neighbour idx is + 2 each time
            tile.construction_slots[idx] = self
        super().__init__("Settlement", owner)
        self.owner.occupied_tiles.update(self.tiles)
        self.owner.victory_points += 1

    def upgrade_to_city(self):
        self.name = "City"
        self.owner.victory_points += 1

class DevelopmentCard(Construction):
    """Mystery card to give players an edge"""

    def __init__(self, owner: Player):
        super().__init__("Development Card", owner)


# 0: 2/4
# 1: 3/5
# 2: 4/0
# 3: 5/1
# 4: 0/2
# 5: 1/3

# print((5 + 2) % 6)
# print(0 % 6)
