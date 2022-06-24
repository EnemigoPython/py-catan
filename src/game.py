from enum import Enum, auto
from typing import List, Dict, TypeVar, Union

class Resource(Enum):
    """Used by players to build construction items"""
    Brick = auto()
    Lumber = auto()
    Ore = auto()
    Grain = auto()
    Wool = auto()

class Player:
    """A player of the game of Catan"""

    def __init__(self):
        self.resources: List[Resource] = []
        self.development_cards: List[DevelopmentCard] = []
        self.controlled_tiles: List[Tile] = []
        self.victory_points = 0

    @property
    def constructions(self):
        return [item for tile in self.controlled_tiles for item in tile.construction_slots if item.owner is self]

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

    def __init__(self, terrain: str, number: int, neighbours: List[Self]=[]):
        self.terrain = terrain
        self.number = number
        self.neighbours = neighbours
        self.resource = self.resource_dict[self.terrain]
        self.construction_slots: List[Construction] = []
        self.road_slots: List[Road] = []
        self.harbour_slot: Union[Harbour, None] = None

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
    def can_build(item: str, player: Player):
        return all(player.resources.count(key) >= val for key, val in Construction.construction_dict[item].items())

    def __init__(self, name: str, owner: Player):
        assert name in self.construction_dict.keys()
        self.name = name
        self.owner = owner

    def __repr__(self):
        return self.name

class Road(Construction):
    """A road to put your wagon on"""

    def __init__(self, owner: Player, tile: Tile):
        self.tile = tile
        self.tile.road_slots.append(self)
        super().__init__("Road", owner)

class SettlementOrCity(Construction):
    """Hybrid class for settlements/cities"""

    def __init__(self, owner: Player, tile: Tile):
        self.tile = tile
        self.tile.construction_slots.append(self)
        super().__init__("Settlement", owner)

    def upgrade_to_city(self):
        self.name = "City"
        self.owner.victory_points += 1

class DevelopmentCard(Construction):
    """Mystery card to give players an edge"""

    def __init__(self, owner: Player):
        super().__init__("Development Card", owner)


player = Player()
player2 = Player()
tile = Tile("Hills", 3)
settlement = SettlementOrCity(player, tile)
settlement2 = SettlementOrCity(player2, tile)
settlement3 = SettlementOrCity(player, tile)
player.controlled_tiles.append(tile)
print(player.constructions)
