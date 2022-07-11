"""This file contains all game logic components as a library"""
from __future__ import annotations
from enum import Enum, auto
from typing import List, Set, Dict, Tuple, Generator
from random import choice, sample, randint

class Resource(Enum):
    """Used by players to build construction items"""
    Brick = auto()
    Lumber = auto()
    Ore = auto()
    Grain = auto()
    Wool = auto()

class Player:
    """A player of the game of Catan"""

    def __init__(self, name: str = "Default"):
        self.name = name
        self.resources: List[Resource] = []
        self.development_cards: List[DevelopmentCard] = []
        self.occupied_tiles: Set[Tile] = set()
        self.victory_points = 0
        self.army_count = 0

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

    def build(self, item: str, tile: Tile | None = None, slot_idx: int | None = None, 
        stack: List[DevelopmentCard] | None = None, costs_resources=True):
        if costs_resources:
            assert Construction.has_resources_for(self, item), 0
            for resource in Construction.construction_dict[item]: 
                self.resources.remove(resource)
        match item:
            case "Road":
                # TODO: this looks patently ridiculous and it's time to abstract it out to a function
                assert any(settlement.owner is self 
                    for settlement in tile.adjacent_settlements(slot_idx)) or \
                    any(road.owner is self for road in tile.adjacent_roads(slot_idx)) or \
                    (tile.construction_slots[slot_idx] is not None and tile.construction_slots[slot_idx].owner \
                    is self), 1
                Road(self, tile, slot_idx)
            case "Settlement":
                assert any(road.owner is self for road in tile.adjacent_roads(slot_idx)), 2
                assert not tile.adjacent_settlements(slot_idx), 3
                SettlementOrCity(self, tile, slot_idx)
            case "Development Card": 
                self.development_cards.append(stack.pop())
            case "City": 
                raise Exception("Cities must be upgraded from Settlements, not built directly")
            case _: 
                raise Exception("Invalid item")

    def use_card(self, development_card: DevelopmentCard, *args):
        assert development_card in self.development_cards
        return_val = development_card.use(*args)
        self.development_cards.remove(development_card)
        if return_val:
            return return_val

    def steal_random_resource(self, victim: Player):
        if len(victim.resources) == 0:
            return
        random_resource = choice(victim.resources)
        self.resources.append(random_resource)
        victim.resources.remove(random_resource)

    def collect_resources(self, number: int):
        self.resources.extend(tile.resource for tile in self.controlled_tiles if tile.check_proc(number))

    @property
    def longest_road(self):
        longest = 0
        checked_roads: List[Road] = []

        def recurse_road_segment(current_road: Road, current_length: int) -> int:
            current_length += 1
            checked_roads.append(current_road)
            paths = [road for road in current_road.locator[0].adjacent_roads(current_road.locator[1]) 
                if road.owner is self and road not in checked_roads]
            if paths:
                return recurse_road_segment(paths[0], current_length)
            else:
                return current_length
            # if len(paths) == 1:
            #     return recurse_road_segment(paths[0], current_length)
            # elif len(paths) > 1:
            #     return sum(sorted((recurse_road_segment(path, current_length) for path in paths), reverse=True)[0:2]) - 1
            # else:
            #     return current_length

        while remaining := [road for road in self.roads if road not in checked_roads]:
            # paths = [road for road in remaining[0].locator[0].adjacent_roads(remaining[0].locator[1]) 
            #     if road.owner is self and road not in checked_roads]
            current = sum(sorted((recurse_road_segment(path, 0) for path in remaining), reverse=True)[0:2]) - 1
            # breakpoint()
            # current = recurse_road_segment(remaining[0], 0)
            longest = max(longest, current)
        return longest

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

    def __init__(self, terrain: str, number: int, neighbours: List[Tile | None] = None, 
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

    def adjacent_roads(self, edge_idx: int) -> List[Road]:
        """
        Return a list of all Roads adjacent to a tile edge
        """
        roads = [self.road_slots[edge_idx-1], self.road_slots[(edge_idx+1)%6]]
        for e, tile in enumerate(self.vertex_neighbours(edge_idx), 1):
            if tile is not None:
                roads.append(tile.road_slots[(edge_idx+e)%6])
        return [road for road in roads if road is not None]

    def adjacent_settlements(self, vertex_idx: int) -> List[SettlementOrCity]:
        """
        Return a list of all Settlements (or Cities) adjacent to a tile vertex
        """
        intersection = [self] + self.vertex_neighbours(vertex_idx)
        return [tile.construction_slots[idx-1] for (tile, idx) in self.slot_idx_gen(intersection, vertex_idx)
            if tile is not None and tile.construction_slots[idx-1] is not None]

    def check_proc(self, number: int):
        return number == self.number and not self.has_robber

    @staticmethod
    def slot_idx_gen(tiles: List[Tile | None], slot_idx: int) -> Generator[Tuple[Tile | None, int]]:
        """
        Returns the correct slot indices for a single point across an intersection of clockwise tiles.
        Input Tiles can be None (shoreline), and these should NOT be omitted for accurate values
        """
        return ((tile, (slot_idx + (e * 2)) % 6) for e, tile in enumerate(tiles))

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
        assert 0 <= slot_idx < 6
        assert tile.road_slots[slot_idx] is None
        self.locator = (tile, slot_idx)
        tile.road_slots[slot_idx] = self
        super().__init__("Road", owner)
        self.owner.occupied_tiles.add(tile)
        opposite_tile = tile.neighbours[slot_idx]
        if opposite_tile is not None: # create mirror reference on opposite tile
            inverted_slot_idx = (slot_idx + 3) % 6
            opposite_tile.road_slots[inverted_slot_idx] = self
            self.owner.occupied_tiles.add(opposite_tile)

class SettlementOrCity(Construction):
    """Hybrid class for settlements/cities"""

    def __init__(self, owner: Player, tile: Tile, slot_idx: int):
        assert 0 <= slot_idx < 6
        assert tile.construction_slots[slot_idx] is None
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

    def __init__(self, card_type: str, owner: Player | None = None, can_use=False):
        self.card_type = card_type
        self.can_use = can_use
        super().__init__("Development Card", owner)

    @staticmethod
    def default_card_stack():
        return sample([
            DevelopmentCard("knight"),
            DevelopmentCard("knight"),
            DevelopmentCard("knight"),
            DevelopmentCard("knight"),
            DevelopmentCard("knight"),
            DevelopmentCard("knight"),
            DevelopmentCard("knight"),
            DevelopmentCard("knight"),
            DevelopmentCard("knight"),
            DevelopmentCard("knight"),
            DevelopmentCard("knight"),
            DevelopmentCard("knight"),
            DevelopmentCard("knight"),
            DevelopmentCard("knight"),
            DevelopmentCard("victory point"),
            DevelopmentCard("victory point"),
            DevelopmentCard("victory point"),
            DevelopmentCard("victory point"),
            DevelopmentCard("victory point"),
            DevelopmentCard("road building"),
            DevelopmentCard("road building"),
            DevelopmentCard("year of plenty"),
            DevelopmentCard("year of plenty"),
            DevelopmentCard("monopoly"),
            DevelopmentCard("monopoly")
        ], k=25)

    def use(self, *args) -> List[Player] | None:
        assert self.can_use
        card_fn_dict = {
            "knight": self.use_knight,
            "victory point": self.use_victory_point,
            "monopoly": self.use_monopoly,
            "road building": self.use_road_building,
            "year of plenty": self.use_year_of_plenty
        }
        return_val = card_fn_dict[self.card_type](*args)
        if return_val:
            return return_val

    def use_knight(self, board: Board, x: int, y: int):
        self.owner.army_count += 1
        target_players = board.move_robber(self.owner, x, y)
        return target_players

    def use_victory_point(self):
        self.owner.victory_points += 1

    def use_road_building(self, tiles: Tuple[Tile, Tile], slots: Tuple[int, int]):
        for tile, slot in zip(tiles, slots):
            self.owner.build("Road", tile, slot, costs_resources=False)

    def use_year_of_plenty(self, resources: Tuple[Resource, Resource]):
        self.owner.resources.extend(resources)

    def use_monopoly(self, players: List[Player], resource: Resource):
        self.owner.resources.extend(res for player in players for res in player.resources if res == resource)
        for player in players:
            player.resources = [res for res in player.resources if res != resource]

class Board:
    """The board represents the 2d playing space of Catan"""
    def __init__(self, config: dict | None = None):
        _config = config or {}
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
        self.tiles: List[List[Tile]] = _config.get("Tiles") or [
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

        self.robber_tile = [tile for layer in self.tiles for tile in layer if tile.has_robber][0]

        for e, layer in enumerate(self.tiles):
            for f, tile in enumerate(layer):
                if f + 1 < len(layer): # link horizontal neighbour
                    east_tile = layer[f+1]
                    tile.neighbours[1] = east_tile
                    east_tile.neighbours[4] = tile
                if e < 4: # link vertical neighbour(s)
                    if e < 2:
                        south_west_tile = self.tiles[e+1][f]
                        tile.neighbours[3] = south_west_tile
                        south_west_tile.neighbours[0] = tile
                        south_east_tile = self.tiles[e+1][f+1]
                        tile.neighbours[2] = south_east_tile
                        south_east_tile.neighbours[5] = tile
                    else:
                        if f > 0:
                            south_west_tile = self.tiles[e+1][f-1]
                            tile.neighbours[3] = south_west_tile
                            south_west_tile.neighbours[0] = tile
                        if f + 1 < len(layer):
                            south_east_tile = self.tiles[e+1][f]
                            tile.neighbours[2] = south_east_tile
                            south_east_tile.neighbours[5] = tile

    def __iter__(self):
        return iter(self.tiles)

    def __len__(self):
        return len(self.tiles)

    def tile_at(self, x: int, y: int):
        return self.tiles[y][x]

    def init_player_position(self, player: Player, settlements: List[Tuple[int, int, int]], 
            roads: List[Tuple[int, int, int]]):
        """Choose starting locations from a global board of tiles"""
        for settlement in settlements:
            board_location = self.tile_at(settlement[0], settlement[1])
            assert not board_location.adjacent_settlements(settlement[2])
            SettlementOrCity(player, board_location, settlement[2])
        for road in roads:
            board_location = self.tile_at(road[0], road[1])
            Road(player, board_location, road[2])

    def move_robber(self, player: Player, x: int, y: int):
        tile = self.tile_at(x, y)
        assert tile is not self.robber_tile
        self.robber_tile.has_robber = False
        tile.has_robber = True
        self.robber_tile = tile
        return list(set(slot.owner for slot in tile.construction_slots if slot is not None and slot.owner is not player))

class Game:
    """Class to encapsulate all global state in a game of Catan"""

    default_names = [
        "Alice",
        "Bob",
        "Charlie",
        "Dennis",
        "Elaine"
    ]
    
    def __init__(self, config: dict | None = None):
        self.round = 1
        self.config = config or {}
        self.board = Board(self.config.get("board"))
        number_of_players = self.config.get("player_number") or 4
        player_names = self.config.get("player_names") or self.default_names
        self.players = [Player(player_names[name]) for name in range(number_of_players)]
        self.current_actor = self.players[0]
        self.development_cards = self.config.get("development_cards") or DevelopmentCard.default_card_stack()
        self.largest_army: Player | None = None
        self.longest_road: Player | None = None

    def __repr__(self):
        sorted_players = sorted(self.players, key=lambda x: x.victory_points, reverse=True)
        return ", ".join(f"{player}: {player.victory_points}" for player in sorted_players)

    @staticmethod
    def dice_roll():
        return randint(1, 6) + randint(1, 6)

    def check_largest_army(self):
        to_beat = self.largest_army.victory_points if self.largest_army is not None else 2
        if self.current_actor.army_count > to_beat:
            if self.largest_army is not None:
                self.largest_army.victory_points -= 2
            self.current_actor.victory_points += 2
            self.largest_army = self.current_actor

    def check_longest_road(self):
        # to_beat = 
        pass

    def next_turn(self):

        actor_idx = self.players.index(self.current_actor)

game = Game()
game.board.init_player_position(game.players[0], [], [(0, 0, 0), (0, 0, 1), (1, 0, 5), (0, 0, 2), (0, 0, 3), (0, 0, 4), (2, 1, 5)])
# breakpoint()
print(game.players[0].longest_road)
# print(game.players[1].longest_road)
