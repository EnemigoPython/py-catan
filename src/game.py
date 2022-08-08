"""This file contains all game logic components as a library"""
from __future__ import annotations
from enum import Enum, auto
from typing import List, Set, Dict, Tuple, Generator, Callable
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
        return set(item for tile in self.controlled_tiles for item in tile.construction_slots 
            if item is not None and item.owner is self)

    @property
    def roads(self):
        return set(item for tile in self.occupied_tiles for item in tile.road_slots 
            if item is not None and item.owner is self)

    @property
    def harbours(self):
        return set(harbour for tile in self.controlled_tiles for harbour in tile.harbour_slots
            if harbour is not None and tile.construction_slots[tile.harbour_slots.index(harbour)]
            in self.constructions)

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
        def recurse_path(current_road: Road, checked_roads: List[Road], forbidden_roads: List[Road], current_length: int):
            checked_roads.append(current_road)
            # forbidden roads are roads that the last road could see, which means they are behind us
            available_roads = [road for road in current_road.adjacent_roads if road not in checked_roads 
                and road not in forbidden_roads]
            if available_roads:
                return max(recurse_path(path, checked_roads, available_roads, current_length+1) for path in available_roads)
            else:
                return current_length, checked_roads
        
        if not self.roads:
            return 0
        checked_roads = []
        longest = 1
        # keep checking until there are no roads to visit: this ensures every path is visited once
        while remaining := [road for road in self.roads if road not in checked_roads]:
            starting_road = remaining[0]
            checked_roads.append(starting_road)
            path_res = {}
            for path in starting_road.adjacent_roads:
                # we might have visited the road during iteration
                if path not in checked_roads:
                    path_length, checked_roads = recurse_path(path, checked_roads, starting_road.adjacent_roads, 2)
                    path_res[str(path)] = path_length
            if not path_res:
                continue
            longest_paths = sorted(path_res.items(), key=lambda x: x[1], reverse=True)[0:2]
            # if the starting road isn't at an edge, it gets counted twice so this needs to be adjusted for
            total = sum(i[1] for i in longest_paths) - (len(longest_paths) - 1)
            get_road = [r for r in starting_road.adjacent_roads if str(r) == longest_paths[0][0]][0]
            if len(longest_paths) > 1:
                get_second_road = [r for r in starting_road.adjacent_roads if str(r) == longest_paths[1][0]][0]
                # if the first road can see the second road, then the starting road is sticking out in a fork (not to be included)
                if get_second_road in get_road.adjacent_roads:
                    total -= 1
            longest = max(longest, total)
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

    def edge_neighbours(self, edge_idx: int):
        """
        Determine, given an edge of the tile, what other tiles are intersected.
        Returned clockwise, includes Nonetype values
        """
        if edge_idx == 0:
            return [self.neighbours[-1], self.neighbours[0], self.neighbours[1]]
        return self.neighbours[edge_idx-1:edge_idx+2]

    def adjacent_roads(self, edge_idx: int) -> List[Road]:
        """
        Return a list of all Roads adjacent to a tile edge
        """
        roads = [road for road in (self.road_slots[edge_idx-1], self.road_slots[(edge_idx+1)%6]) if road is not None]
        for e, tile in enumerate(self.edge_neighbours(edge_idx), 1):
            if tile is None:
                continue
            if e < 3:
                road_slot = tile.road_slots[(edge_idx+e)%6]
                if road_slot is not None and road_slot not in roads:
                    roads.append(road_slot)
            if e > 1:
                road_slot = tile.road_slots[(edge_idx+e+2)%6]
                if road_slot is not None and road_slot not in roads:
                    roads.append(road_slot)
        return roads

    def adjacent_settlements(self, vertex_idx: int) -> List[SettlementOrCity]:
        """
        Return a list of all Settlements (or Cities) adjacent to a tile vertex
        """
        intersection = [self] + self.vertex_neighbours(vertex_idx)
        settlements = []
        for tile, idx in self.slot_idx_gen(intersection, vertex_idx):
            if tile is None:
                continue
            construction_slots = tile.construction_slots[idx-1], tile.construction_slots[(idx+1)%6]
            settlements.extend(slot for slot in construction_slots if slot is not None and slot not in settlements)
        return settlements

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

    def __repr__(self):
        return f"{super().__repr__()} at {self.locator}"

    @property
    def adjacent_roads(self):
        return self.locator[0].adjacent_roads(self.locator[1])

    def road_is(self, road: Road):
        """
        """

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
    def __init__(self, **kwargs):
        harbours = kwargs.get("harbours") or [
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
        self.tiles: List[List[Tile]] = kwargs.get("Tiles") or [
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
    
    def __init__(self, **kwargs):
        self.round = 1
        self.board = Board(board=kwargs.get("board"))
        number_of_players = kwargs.get("player_number", 4)
        player_names = kwargs.get("player_names", self.default_names)
        self.players = [Player(player_names[name]) for name in range(number_of_players)]
        self.current_actor = self.players[0]
        self.development_cards = kwargs.get("development_cards", DevelopmentCard.default_card_stack())
        self.player_with_largest_army: Player | None = None
        self.player_with_longest_road: Player | None = None

    def __repr__(self):
        sorted_players = sorted(self.players, key=lambda x: x.victory_points, reverse=True)
        return ", ".join(f"{player}: {player.victory_points}" for player in sorted_players)

    @staticmethod
    def dice_roll():
        return randint(1, 6) + randint(1, 6)

    def check_largest_army(self):
        to_beat = self.player_with_largest_army.army_count if self.player_with_largest_army is not None else 2
        if self.current_actor.army_count > to_beat:
            if self.player_with_largest_army is not None:
                self.player_with_largest_army.victory_points -= 2
            self.current_actor.victory_points += 2
            self.player_with_largest_army = self.current_actor

    def check_longest_road(self):
        to_beat = self.player_with_longest_road.longest_road if self.player_with_longest_road is not None else 2
        if self.current_actor.longest_road > to_beat:
            if self.player_with_longest_road is not None:
                self.player_with_longest_road.victory_points -= 2
            self.current_actor.victory_points += 2
            self.player_with_longest_road = self.current_actor

    def next_turn(self):
        actor_idx = self.players.index(self.current_actor)
        self.current_actor = self.players[(actor_idx+1)%len(self.players)]

    def is_winner(self) -> bool | Player:
        """
        If no winner, return False.
        If there is a winner, return Player.
        Use as a game loop like so: `while not (winner := game.is_winner()):`
        """
        return False if self.current_actor.victory_points < 10 else self.current_actor

    def game_wrapper(self, option: Callable):
        """
        This wrapper function is called to create a game loop and handle internal state.
        `option`: a function to be called on the Player inherited instances in `self.players` created by `__init__`.
        For example, the AI will insert controller code in here to play its turn, but an input can also be retrieved from a human.
        """
        pass
