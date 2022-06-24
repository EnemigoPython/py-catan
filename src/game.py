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
        """Find all tiles that the player has settled, and not just put roads on"""
        return [tile for tile in self.occupied_tiles 
            if any(c is not None and c.owner is self for c in tile.construction_slots)]

    @property
    def constructions(self):
        """Find all constructions made by the player"""
        # cast to a set to eliminate duplicate references, then back to a list for indexing
        return list(set(item for tile in self.controlled_tiles for item in tile.construction_slots 
            if item is not None and item.owner is self))

    @property
    def roads(self):
        return list(set(item for tile in self.occupied_tiles for item in tile.road_slots 
            if item is not None and item.owner is self))

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

    def __init__(self, terrain: str, number: int, neighbours: List[Self | None]=None, harbour=None):
        self.terrain = terrain
        self.number = number
        assert neighbours is None or len(neighbours) <= 6
        self.neighbours = neighbours or [None for _ in range(6)]
        self.resource = self.resource_dict[self.terrain]
        self.construction_slots: List[Construction | None] = [None for _ in range(6)]
        self.road_slots: List[Road | None] = [None for _ in range(6)]
        self.harbour_slot: Harbour | None = harbour

    def __repr__(self):
        return self.terrain

    def vertex_neighbour(self, vertex_idx: int):
        """Determine, given a vertex of the tile, what other tiles are intersected"""
        if vertex_idx == 0:
            return self.neighbours[6:0:-4]
        return self.neighbours[vertex_idx-1:vertex_idx+1]


    def check_proc(self, number: int):
        return self.resource if number == self.number else None

    @staticmethod
    def create_board(config=None):
        """Method to generate a board of linked tiles; returned as matrix"""
    # if config.get("Tiles") is None:
        tiles: List[List[Tile]] = [
            [
                Tile("Mountains", 10),
                Tile("Pasture", 2),
                Tile("Forest", 9)
            ],
            [
                Tile("Fields", 12),
                Tile("Hills", 6),
                Tile("Pasture", 4),
                Tile("Hills", 10)
            ],
            [
                Tile("Fields", 9),
                Tile("Forest", 11),
                Tile("Desert", 0),
                Tile("Forest", 3),
                Tile("Mountains", 8)
            ],
            [
                Tile("Forest", 8),
                Tile("Mountains", 3),
                Tile("Fields", 4),
                Tile("Pasture", 5)
            ],
            [
                Tile("Hills", 5),
                Tile("Fields", 6),
                Tile("Pasture", 11)
            ]
        ]

        for e, layer in enumerate(tiles):
            for f, tile in enumerate(layer):
                if f + 1 < len(layer): # link horizontal neighbour
                    east_tile = layer[f+1]
                    tile.neighbours[1] = east_tile
                    east_tile.neighbours[4] = tile
                if e < 4: # link vertical neighbour(s)
                    if e < 2:
                        south_west_tile = tiles[e+1][f]
                        tile.neighbours[3] = south_west_tile
                        south_west_tile.neighbours[0] = tile
                        south_east_tile = tiles[e+1][f+1]
                        tile.neighbours[2] = south_east_tile
                        south_east_tile.neighbours[5] = tile
                    else:
                        if f > 0:
                            south_west_tile = tiles[e+1][f-1]
                            tile.neighbours[3] = south_west_tile
                            south_west_tile.neighbours[0] = tile
                        if f + 1 < len(layer):
                            south_east_tile = tiles[e+1][f]
                            tile.neighbours[2] = south_east_tile
                            south_east_tile.neighbours[5] = tile
        return tiles

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
        self.tiles = [tile] + tile.vertex_neighbour(slot_idx)
        for e, tile in enumerate(self.tiles):
            # None is left in the loop so that the idx is calculated correctly
            if tile is None: continue
            idx = (slot_idx + (e * 2)) % 6  # vertices are returned clockwise; neighbour idx is + 2 each time
            tile.construction_slots[idx] = self
        self.tiles: List[Tile] = [tile for tile in self.tiles if tile is not None] # once the loop has completed eliminate NoneTypes
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
board = Tile.create_board()
