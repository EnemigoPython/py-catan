"""This file contains all game logic components as a library"""
from __future__ import annotations
from enum import Enum, auto
from typing import List, Set, Dict, Tuple, Generator

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

    @property
    def harbours(self):
        return list(set(harbour for tile in self.controlled_tiles for harbour in tile.harbour_slots
            if harbour is not None and tile.construction_slots[tile.harbour_slots.index(harbour)]
            in self.constructions))

    def __repr__(self):
        return self.name

    def init_position(self, board: List[List[Tile]], settlements: List[Tuple[int, int, int]], 
            roads: List[Tuple[int, int, int]]):
        """Choose starting locations from a global board of tiles"""
        for settlement in settlements:
            board_location = board[settlement[1]][settlement[0]]
            SettlementOrCity(self, board_location, settlement[2])
        for road in roads:
            board_location = board[road[1]][road[0]]
            Road(self, board_location, road[2])

    def build(self, item: str, tile: Tile | None = None, slot_idx: int | None = None):
        assert Construction.has_resources_for(self, item)
        match item:
            case "Road":
                print(tile.adjacent_roads(slot_idx), tile.adjacent_settlements(slot_idx))
                assert any(settlement.owner is self 
                    for settlement in tile.adjacent_settlements(slot_idx)) or \
                    any(road.owner is self for road in tile.adjacent_roads(slot_idx))
                Road(self, tile, slot_idx)
            case "Settlement":
                assert any(road.owner is self for road in Road.adjacent_roads(tile, slot_idx))
                assert not tile.adjacent_settlements(slot_idx)
                SettlementOrCity(self, tile, slot_idx)
            case "Development Card": pass
            case "City": raise Exception("Cities must be upgraded from Settlements, not built directly")
        for item in Construction.construction_dict[item]: self.resources.remove(item)

class Harbour:
    """A trading port that can be used for better deals"""
    
    def __init__(self, resource=None):
        self.rate = 3 if resource is None else 2
        self.resource: Resource | None = resource

    def __repr__(self):
        return f"{self.resource.name if self.resource else 'General'} Harbour"

class Tile:
    """A single tile on the Catan game board"""

    resource_dict: Dict[str, str | None] = {
        "Desert": None,
        "Hills": Resource.Brick,
        "Forest": Resource.Lumber,
        "Mountains": Resource.Ore,
        "Fields": Resource.Grain,
        "Pasture": Resource.Wool
    }

    def __init__(self, terrain: str, number: int, neighbours: List[Tile|None] = None, 
            harbours: List[Tuple[Harbour, int]] = None, has_robber=False):
        self.terrain = terrain
        self.number = number
        assert neighbours is None or len(neighbours) <= 6
        self.neighbours = neighbours or [None for _ in range(6)]
        self.resource = self.resource_dict[self.terrain]
        self.construction_slots: List[Construction | None] = [None for _ in range(6)]
        self.road_slots: List[Road | None] = [None for _ in range(6)]
        self.harbour_slots: List[Harbour | None] = [None for _ in range(6)]
        if harbours:
            for harbour, slot in harbours:
                assert 0 <= slot < 6
                self.harbour_slots[slot] = harbour
        self.has_robber = has_robber

    def __repr__(self):
        return f"{self.terrain} ({self.number})"

    def vertex_neighbours(self, vertex_idx: int):
        """
        Determine, given a vertex of the tile, what other tiles are intersected.
        Returned clockwise, includes Nonetype values
        """
        if vertex_idx == 0:
            return self.neighbours[6::-5]
        return self.neighbours[vertex_idx-1:vertex_idx+1]

    def adjacent_roads(self, edge_idx: int):
        """
        Return a list of all Roads adjacent to a tile edge
        """
        roads = [self.road_slots[edge_idx-1], self.road_slots[(edge_idx+1)%6]]
        for e, tile in enumerate(self.vertex_neighbours(edge_idx), 1):
            if tile is not None:
                roads.append(tile.road_slots[(edge_idx+e)%6])
        return [road for road in roads if road is not None]

    def adjacent_settlements(self, vertex_idx: int):
        """
        Return a list of all Settlements (or Cities) adjacent to a tile vertex
        """
        intersect = [self] + self.vertex_neighbours(vertex_idx)
        settlements = []
        for tile, idx in self.slot_idx_gen(intersect, vertex_idx):
            if tile is not None and tile.construction_slots[idx-1] is not None:
                settlements.append(tile.construction_slots[idx-1])
        return settlements

    def edge_neighbours(self, edge_idx: int):
        """
        Determine, given an edge of the tile, what other tiles are intersected.
        Returned clockwise
        """
        return self.vertex_neighbours(edge_idx) + self.vertex_neighbours((edge_idx+1)%6)[-1::]

    def check_proc(self, number: int):
        return self.resource if number == self.number else None

    @staticmethod
    def slot_idx_gen(tiles: List[Tile | None], slot_idx: int) -> Generator[Tuple[Tile | None, int]]:
        """
        Returns the correct slot for a single point across an intersection of clockwise tiles.
        Input Tiles can be None (thin air), and these should NOT be omitted for accurate values
        """
        return ((tile, (slot_idx + (e * 2)) % 6) for e, tile in enumerate(tiles))

    @staticmethod
    def create_board(config=None):
        """Method to generate a board of linked tiles; returned as matrix"""
        _config: dict = config or {}
        harbours = _config.get("harbours") or [
            Harbour(),
            Harbour(Resource.Grain),
            Harbour(Resource.Ore),
            Harbour(Resource.Lumber),
            Harbour(Resource.Brick),
            Harbour(),
            Harbour(Resource.Wool),
            Harbour(),
            Harbour()
        ]
        tiles: List[List[Tile]] = _config.get("Tiles") or [
            [
                Tile("Mountains", 10, harbours=[(harbours[0], 0), (harbours[0], 5)]),
                Tile("Pasture", 2, harbours=[(harbours[1], 0), (harbours[1], 1)]),
                Tile("Forest", 9, harbours=[(harbours[2], 2), (harbours[1], 5)])
            ],
            [
                Tile("Fields", 12, harbours=[(harbours[3], 4), (harbours[3], 5)]),
                Tile("Hills", 6),
                Tile("Pasture", 4),
                Tile("Hills", 10, harbours=[(harbours[2], 0), (harbours[2], 1)])
            ],
            [
                Tile("Fields", 9, harbours=[(harbours[3], 0), (harbours[4], 3)]),
                Tile("Forest", 11),
                Tile("Desert", 0, has_robber=True),
                Tile("Forest", 3),
                Tile("Mountains", 8, harbours=[(harbours[5], 1), (harbours[5], 2)])
            ],
            [
                Tile("Forest", 8, harbours=[(harbours[3], 4), (harbours[3], 5)]),
                Tile("Mountains", 3),
                Tile("Fields", 4),
                Tile("Pasture", 5, harbours=[(harbours[6], 2), (harbours[6], 3)])
            ],
            [
                Tile("Hills", 5, harbours=[(harbours[7], 3), (harbours[7], 4)]),
                Tile("Fields", 6, harbours=[(harbours[8], 2), (harbours[8], 3)]),
                Tile("Pasture", 11, harbours=[(harbours[6], 1), (harbours[8], 4)])
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
    def has_resources_for(player: Player, item: str):
        """Method to check if a player has the correct resources to construct a given item"""
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
        opposite_tile = tile.neighbours[slot_idx]
        if opposite_tile is not None: # create mirror reference on opposite tile
            inverted_slot_idx = (slot_idx + 3) % 6
            assert opposite_tile.road_slots[inverted_slot_idx] is None
            opposite_tile.road_slots[inverted_slot_idx] = self
            self.owner.occupied_tiles.add(opposite_tile)

class SettlementOrCity(Construction):
    """Hybrid class for settlements/cities"""

    def __init__(self, owner: Player, tile: Tile, slot_idx: int):
        assert 0 <= slot_idx < 6 and tile.construction_slots[slot_idx] is None
        self.tiles = [tile] + tile.vertex_neighbours(slot_idx)
        for tile, idx in Tile.slot_idx_gen(self.tiles, slot_idx):
            if tile is not None:
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
# # print(x[6::-5])

player = Player("Alice")
player.resources.extend([
    Resource.Brick, 
    Resource.Lumber
])
player.init_position(board, [(1, 1, 4)], [(1, 1, 5)])
# print(board[1][1].edge_neighbours(0))
# print(board[1][1].edge_neighbours(1))
# print(board[1][1].edge_neighbours(2))
print(board[1][1].edge_neighbours(3))
print(board[1][1].edge_neighbours(4))
print(board[1][1].edge_neighbours(5))
# print(board[1][0].adjacent_roads(1))
print(board[1][0].adjacent_roads(2))
print(board[1][0].adjacent_settlements(3))
# player.build("Settlement", board[0][0], 2)
# index Hills 6 -> 5
# Fields 12 -> 1
# Mountains 10 -> 1

# slot_idx + (e * 2)) % 6)
