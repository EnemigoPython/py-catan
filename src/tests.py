"""Tests to run via pytest"""
from game import *

class TestClass:
    def test_resources(self):
        tile = Tile("Hills", 3)
        assert not tile.check_proc(5)
        assert tile.check_proc(3)

    def test_construction(self):
        road = Construction("Road", owner=Player())
        assert str(road) == "Default's Road"
        try:
            Construction("Invalid", owner=Player())
            raise Exception("This should not be ok")
        except AssertionError:
            pass

    def test_construction_has_resources(self):
        player = Player()
        player.resources.append(Resource.Brick)
        assert not Construction.has_resources_for(player, "Road")
        player.resources.append(Resource.Lumber)
        assert Construction.has_resources_for(player, "Road")
        player.resources = [
            Resource.Ore, 
            Resource.Ore, 
            Resource.Ore, 
            Resource.Grain,
            Resource.Grain 
        ]
        assert Construction.has_resources_for(player, "City")
        player.resources.pop()
        assert not Construction.has_resources_for(player, "City")
        assert not Construction.has_resources_for(player, "Development Card")

    def test_construction_slot(self):
        tile = Tile("Hills", 3)
        settlement1 = SettlementOrCity(Player(), tile, 0)
        assert tile.construction_slots[0] is settlement1
        assert tile.construction_slots[1] is None
        settlement2 = SettlementOrCity(Player(), tile, 1)
        assert tile.construction_slots[1] is settlement2
        try:
            _ = SettlementOrCity(Player(), tile, 1)
            Exception("Not allowed to build on a used slot")
        except AssertionError:
            pass
        try:
            _ = SettlementOrCity(Player(), tile, 6)
            Exception("Also not allowed to build on invalid index")
        except AssertionError:
            pass
        road = Road(Player(), tile, 1)
        assert tile.road_slots[1] is road

    def test_player_controlled_construction(self):
        player1 = Player("Alice")
        tile = Tile("Hills", 3)
        _ = SettlementOrCity(player1, tile, 0)
        assert len(player1.constructions) == 1
        _ = SettlementOrCity(player1, tile, 1)
        assert len(player1.constructions) == 2
        player2 = Player("Bob")
        _ = SettlementOrCity(player2, tile, 2)
        assert len(player1.constructions) == 2
        print(str(player2.constructions))
        assert "Bob's Settlement" in [str(c) for c in player2.constructions]
        _ = Road(player1, tile, 0)
        assert len(player1.roads) == 1

    def test_board_init(self):
        board = Board()
        assert len(board) == 5
        assert sum(len(l) for l in board) == 19
        assert str(board.tile_at(0, 0)) == "Mountains (10)"
        assert board.tile_at(0, 0).neighbours == [None, board.tile_at(1, 0), board.tile_at(1, 1), board.tile_at(0, 1), None, None]
        assert board.tile_at(0, 0).neighbours[1].neighbours[4] == board.tile_at(0, 0)
        assert board.tile_at(1, 0).neighbours == [
            None, 
            board.tile_at(2, 0), 
            board.tile_at(2, 1), 
            board.tile_at(1, 1), 
            board.tile_at(0, 0), 
            None
        ]
        assert [str(i) for i in board.tile_at(3, 1).neighbours] == [
            "None", 
            "None", 
            "Mountains (8)", 
            "Forest (3)", 
            "Pasture (4)", 
            "Forest (9)"
        ]
        assert [str(i) for i in board.tile_at(1, 1).neighbours] == [
            "Pasture (2)", 
            "Pasture (4)", 
            "Desert (0)", 
            "Forest (11)", 
            "Fields (12)", 
            "Mountains (10)"
        ]
        assert [i.number for i in board.tile_at(2, 2).neighbours] == [4, 3, 4, 3, 11, 6]
        assert [str(i) for i in board.tile_at(0, 3).neighbours] == [
            "Forest (11)", 
            "Mountains (3)", 
            "Hills (5)", 
            "None", 
            "None", 
            "Fields (9)"
        ]
        assert [i.number for i in board.tile_at(2, 3).neighbours] == [3, 5, 11, 6, 3, 0]
        assert [str(i) for i in board.tile_at(3, 3).neighbours] == [
            "Mountains (8)", 
            "None", 
            "None", 
            "Pasture (11)", 
            "Fields (4)", 
            "Forest (3)"
        ]
        assert [str(i) for i in board.tile_at(0, 4).neighbours] == [
            "Mountains (3)", 
            "Fields (6)", 
            "None", 
            "None", 
            "None", 
            "Forest (8)"
        ]
        assert [str(i) for i in board.tile_at(2, 4).neighbours] == [
            "Pasture (5)", 
            "None", 
            "None", 
            "None", 
            "Fields (6)", 
            "Fields (4)"
        ]

    # TODO: how necessary is a reference to tiles on Construction anyway?
    # Seems like it might be a pointless binding as the Player can already find
    # all the tiles he owns using controlled_tiles. Might be removed soon, in which
    # case this test should look at construction_slots instead of Construction.tiles
    def test_board_construction_multiple_tiles(self):
        player = Player("Alice")
        board = Board()
        settlement = SettlementOrCity(player, board.tile_at(0, 0), 2)
        assert len(settlement.tiles) == 3
        assert all(tile in settlement.tiles for tile in (board.tile_at(0, 0), board.tile_at(1, 0), board.tile_at(1, 1)))
        assert board.tile_at(1, 0).construction_slots[4] is settlement
        assert board.tile_at(1, 1).construction_slots[0] is settlement
        settlement2 = SettlementOrCity(player, board.tile_at(0, 2), 4)
        assert len(settlement2.tiles) == 1
        assert settlement2.tiles[0] is board.tile_at(0, 2)
        settlement3 = SettlementOrCity(player, board.tile_at(0, 2), 0)
        assert len(settlement3.tiles) == 2
        assert board.tile_at(0, 1).construction_slots[4] is settlement3
        settlement4 = SettlementOrCity(player, board.tile_at(0, 4), 1)
        assert len(settlement4.tiles) == 3
        tile_numbers = [tile.number for tile in settlement4.tiles]
        assert all(num in tile_numbers for num in (3, 5, 6))
        assert len(player.constructions) == 4
        settlement5 = SettlementOrCity(player, board.tile_at(4, 2), 5)
        assert len(settlement5.tiles) == 3
        tile_names = [str(tile) for tile in settlement5.tiles]
        assert all(name in tile_names for name in ("Hills (10)", "Forest (3)", "Mountains (8)"))

    def test_harbours_on_created_board(self):
        board = Board()
        assert sum(1 for _ in (harbour for layer in board for tile in layer for harbour in tile.harbour_slots 
            if isinstance(harbour, Harbour))) == 24 # uses of harbour (by multiple tiles)
        assert len(set(harbour for layer in board for tile in layer for harbour in tile.harbour_slots 
            if isinstance(harbour, Harbour))) == 9 # harbour instances
        assert len([slot for slot in board.tile_at(0, 0).harbour_slots if slot is not None]) == 2
        assert str(board.tile_at(0, 0).harbour_slots[0]) == "General Harbour"
        assert board.tile_at(0, 0).harbour_slots[0] is board.tile_at(0, 0).harbour_slots[5]
        assert str(board.tile_at(2, 0).harbour_slots[2]) == "Ore Harbour"
        assert board.tile_at(2, 0).harbour_slots[2] is board.tile_at(3, 1).harbour_slots[0]

    def test_player_owned_harbours(self):
        players = [Player("Alice"), Player("Bob"), Player("Charlie")]
        board = Board()
        assert len(players[0].harbours) == 0
        SettlementOrCity(players[0], board.tile_at(0, 0), 0)
        assert 3 in (harbour.rate for harbour in players[0].harbours)
        SettlementOrCity(players[0], board.tile_at(0, 0), 4)
        assert len(players[0].harbours) == 1
        SettlementOrCity(players[1], board.tile_at(2, 0), 4)
        assert len(players[1].harbours) == 0
        SettlementOrCity(players[1], board.tile_at(2, 0), 2)
        assert Resource.Ore in (harbour.resource for harbour in players[1].harbours)
        SettlementOrCity(players[1], board.tile_at(2, 4), 1)
        assert len(players[1].harbours) == 2
        resources = set(harbour.resource for harbour in players[1].harbours)
        assert Resource.Wool in resources
        SettlementOrCity(players[2], board.tile_at(0, 4), 1)
        SettlementOrCity(players[1], board.tile_at(0, 4), 3)
        assert board.tile_at(0, 4).harbour_slots[3].rate == 3
        assert len(players[2].harbours) == 0

    def test_init_player_position_method(self):
        players = [Player("Alice"), Player("Bob"), Player("Charlie"), Player("Dennis")]
        board = Board()
        board.init_player_position(players[0], [(0, 1, 2), (3, 2, 2)], [(0, 1, 2), (3, 2, 1)])
        assert len(players[0].constructions) == 2
        assert len(players[0].roads) == 2
        assert len(players[0].harbours) == 0
        tile_types = set(tile.terrain for tile in players[0].controlled_tiles)
        assert all(terrain in tile_types for terrain in ("Forest", "Fields", "Hills", "Mountains", "Pasture"))
        board.init_player_position(players[1], [(2, 1, 1), (1, 4, 0)], [(2, 1, 0), (1, 4, 0)])
        assert sum(1 for _ in (tile for tile in players[1].controlled_tiles if tile.terrain == "Fields")) == 2
        assert sum(1 for _ in (tile for tile in players[1].controlled_tiles if tile.number == 4)) == 2
        board.init_player_position(players[2], [(3, 3, 3)], [])
        assert len(players[2].constructions) == 1
        assert len(players[2].roads) == 0
        assert len(players[2].controlled_tiles) == 2
        assert len(players[2].occupied_tiles) == 2
        assert len(players[2].harbours) == 1
        try:
            board.init_player_position(players[3], [(3, 3, 3)], [])
            raise Exception("Not allowed")
        except AssertionError:
            pass

    def test_mirrored_road_slot(self):
        players = [Player("Alice"), Player("Bob"), Player("Charlie")]
        board = Board()
        board.init_player_position(players[0], [], [(0, 1, 2)])
        assert board.tile_at(0, 1).road_slots[2] is not None
        assert board.tile_at(0, 1).road_slots[2] is board.tile_at(1, 2).road_slots[5]
        assert len(players[0].occupied_tiles) == 2
        assert len(players[0].controlled_tiles) == 0
        SettlementOrCity(players[0], board.tile_at(0, 1), 3)
        assert len(players[0].occupied_tiles) == 3
        assert len(players[0].controlled_tiles) == 3
        board.init_player_position(players[1], [], [(0, 0, 0)])
        assert len(players[1].occupied_tiles) == 1
        board.init_player_position(players[2], [], [(1, 0, 1)])
        try:
            Road(players[2], board.tile_at(2, 0), 4)
            raise Exception("This is the mirrored position of the road we placed")
        except AssertionError:
            pass

    def test_adjacent_roads_detection(self):
        players = [Player("Alice"), Player("Bob"), Player("Charlie")]
        board = Board()
        board.init_player_position(players[0], [], [(1, 1, 5), (2, 0, 1), (3, 1, 0)])
        assert len(board.tile_at(1, 1).adjacent_roads(4)) == 1
        assert len(board.tile_at(1, 1).adjacent_roads(5)) == 0
        assert len(board.tile_at(1, 0).adjacent_roads(4)) == 1
        assert len(board.tile_at(1, 0).adjacent_roads(3)) == 1
        assert len(board.tile_at(0, 1).adjacent_roads(0)) == 1
        assert len(board.tile_at(0, 0).adjacent_roads(3)) == 1
        roads = board.tile_at(2, 0).adjacent_roads(1)[0], board.tile_at(3, 1).adjacent_roads(0)[0]
        assert str(roads[0]) == "Alice's Road at (Hills (10), 0)"
        assert str(roads[1]) == "Alice's Road at (Forest (9), 1)"
        board.init_player_position(players[1], [], [(2, 2, 5), (2, 1, 3)])
        assert len(board.tile_at(2, 2).adjacent_roads(5)) == 1
        assert len(board.tile_at(1, 1).adjacent_roads(2)) == 1
        assert len(board.tile_at(2, 1).adjacent_roads(4)) == 2
        board.init_player_position(players[2], [], [(1, 3, 0), (2, 3, 5), (1, 3, 2), (2, 3, 3), (2, 3, 4), (4, 2, 2)])
        assert len(board.tile_at(1, 3).adjacent_roads(1)) == 4
        assert len(board.tile_at(1, 3).adjacent_roads(2)) == 2
        road_slot = board.tile_at(3, 3).road_slots[1]
        assert road_slot is None
        assert len(board.tile_at(3, 3).adjacent_roads(1)) == 1
        road = board.tile_at(3, 3).adjacent_roads(1)[0]
        assert str(road) == "Charlie's Road at (Mountains (8), 2)"

    def test_adjacent_settlements_detection(self):
        players = [Player("Alice"), Player("Bob"), Player("Charlie")]
        board = Board()
        board.init_player_position(players[0], [(1, 1, 4), (0, 0, 2)], [])
        assert len(board.tile_at(0, 0).adjacent_settlements(3)) == 2
        assert len(board.tile_at(1, 0).adjacent_settlements(3)) == 1
        assert len(board.tile_at(1, 1).adjacent_settlements(2)) == 0
        board.init_player_position(players[1], [(1, 2, 2)], [])
        assert len(board.tile_at(1, 2).adjacent_settlements(1)) == 2
        adjacent_settlements = [str(s) for s in board.tile_at(1, 2).adjacent_settlements(1)]
        assert all(s in adjacent_settlements for s in ("Alice's Settlement", "Bob's Settlement"))
        board.init_player_position(players[2], [(1, 1, 2), (4, 2, 1)], [])
        assert len(board.tile_at(1, 2).adjacent_settlements(1)) == 3
        adjacent_settlements = set(str(s) for s in board.tile_at(1, 2).adjacent_settlements(1))
        assert len(adjacent_settlements) == 3
        assert len(board.tile_at(4, 2).adjacent_settlements(2)) == 1
        assert len(board.tile_at(4, 2).adjacent_settlements(0)) == 1

    def test_build_road_method(self):
        players = [Player("Alice"), Player("Bob")]
        board = Board()
        for _ in range(7):
            players[0].resources.extend([
                Resource.Brick, 
                Resource.Lumber, 
            ])
        board.init_player_position(players[0], [(0, 1, 2), (3, 2, 2)], [(3, 2, 1)])
        players[0].build("Road", board.tile_at(0, 1), 2)
        players[0].build("Road", board.tile_at(0, 1), 3)
        players[0].build("Road", board.tile_at(0, 1), 4)
        players[0].build("Road", board.tile_at(0, 2), 1)
        players[0].build("Road", board.tile_at(4, 2), 5)
        players[0].build("Road", board.tile_at(1, 2), 3)
        try:
            players[0].build("Road", board.tile_at(4, 2), 1)
            raise Exception("This road isn't connected to anything")
        except AssertionError as e:
            assert e.args[0] == 1
        board.init_player_position(players[1], [(0, 4, 1)], [])
        players[1].resources.extend([Resource.Brick, Resource.Lumber])
        try:
            players[1].build("Road", board.tile_at(4, 2), 0)
            raise Exception("Bob doesn't own the adjacent road")
        except AssertionError as e:
            assert e.args[0] == 1

    def test_longest_road(self):
        players = [Player("Alice"), Player("Bob"), Player("Charlie")]
        board = Board()
        for _ in range(6):
            players[0].resources.extend([
                Resource.Brick, 
                Resource.Lumber, 
            ])
        board.init_player_position(players[0], [(0, 1, 3)], [(0, 0, 0), (0, 0, 1)])
        assert players[0].longest_road == 2
        players[0].build("Road", board.tile_at(0, 1), 3)
        assert players[0].longest_road == 2
        players[0].build("Road", board.tile_at(0, 0), 2)
        players[0].build("Road", board.tile_at(0, 0), 3)
        assert players[0].longest_road == 4
        players[0].build("Road", board.tile_at(1, 0), 3)
        assert players[0].longest_road == 4
        players[0].build("Road", board.tile_at(2, 1), 4)
        assert players[0].longest_road == 4
        players[0].build("Road", board.tile_at(2, 1), 3)
        assert players[0].longest_road == 5
        board.init_player_position(players[1], [], [
            (2, 0, 0), 
            (2, 0, 1), 
            (3, 1, 0), 
            (3, 1, 1), 
            (4, 2, 0), 
            (4, 2, 1), 
            (4, 2, 2),
            (3, 3, 1),
            (3, 3, 2),
            (2, 4, 1),
            (2, 4, 2)
        ])
        assert players[1].longest_road == 11
        for _ in range(3):
            players[1].resources.extend([
                Resource.Brick, 
                Resource.Lumber, 
            ])
        players[1].build("Road", board.tile_at(3, 1), 2)
        # TODO: this fails because `available_roads` should only include the side of adjacent roads opposite to path entry
        assert players[1].longest_road == 11
        players[1].build("Road", board.tile_at(2, 4), 3)
        assert players[1].longest_road == 12

    def test_build_settlement_method(self):
        players = [Player("Alice"), Player("Bob"), Player("Charlie")]
        board = Board()
        for _ in range(2):
            players[0].resources.extend([
                Resource.Brick,
                Resource.Lumber,
                Resource.Wool,
                Resource.Grain
            ])
        board.init_player_position(players[0], [(0, 1, 2), (3, 2, 2)], [(0, 1, 2), (0, 1, 3), (3, 2, 1)])
        players[0].build("Settlement", board.tile_at(0, 1), 4)
        try:
            players[0].build("Settlement", board.tile_at(0, 1), 3)
            raise Exception("This is too close to existing settlements")
        except AssertionError as e:
            assert e.args[0] == 3
        board.init_player_position(players[1], [(0, 0, 1)], [(0, 0, 1), (1, 1, 0)])
        players[1].resources.extend([
                Resource.Brick,
                Resource.Lumber,
                Resource.Wool,
                Resource.Grain
        ])
        players[1].build("Settlement", board.tile_at(1, 1), 1)
        board.init_player_position(players[2], [(2, 3, 3)], [(2, 3, 0), (2, 3, 1), (2, 3, 2)])
        for _ in range(3):
            players[2].resources.extend([
                Resource.Brick,
                Resource.Lumber,
                Resource.Wool,
                Resource.Grain
            ])
        try:
            players[2].build("Settlement", board.tile_at(2, 3), 1)
            raise Exception("Alice's settlement is too close")
        except AssertionError as e:
            assert e.args[0] == 3
        players[2].build("Settlement", board.tile_at(2, 3), 0)
        try:
            players[2].build("Settlement", board.tile_at(2, 4), 3)
            raise Exception("There are no roads connecting this point")
        except AssertionError as e:
            assert e.args[0] == 2

    def test_use_development_cards(self):
        players = [Player("Alice"), Player("Bob")]
        players[0].development_cards.append(DevelopmentCard("victory point", players[0], can_use=True))
        players[0].development_cards.append(DevelopmentCard("year of plenty", players[0], can_use=True))
        players[0].development_cards.append(DevelopmentCard("knight", players[0], can_use=True))
        players[0].development_cards.append(DevelopmentCard("road building", players[0], can_use=True))
        players[0].development_cards.append(DevelopmentCard("monopoly", players[0], can_use=True))
        players[0].use_card(players[0].development_cards[0])
        assert players[0].victory_points == 1
        assert len(players[0].development_cards) == 4
        players[0].use_card(players[0].development_cards[0], [Resource.Grain, Resource.Wool])
        assert players[0].resources == [Resource.Grain, Resource.Wool]
        board = Board()
        board.init_player_position(players[0], [(0, 0, 1), (1, 1, 1)], [])
        board.init_player_position(players[1], [(1, 1, 4)], [])
        players[1].resources = [Resource.Brick, Resource.Brick, Resource.Brick, Resource.Wool]
        assert board.tile_at(2, 2).has_robber
        potential_targets = players[0].use_card(players[0].development_cards[0], board, 1, 1)
        assert len(potential_targets) == 1
        assert board.tile_at(1, 1).has_robber
        assert not board.tile_at(2, 2).has_robber
        players[0].steal_random_resource(potential_targets[0])
        assert len(players[1].resources) == 3
        players[0].use_card(players[0].development_cards[0], (board.tile_at(0, 0), board.tile_at(0, 0)), (1, 2))
        assert None not in board.tile_at(0, 0).road_slots[1:3]
        players[0].use_card(players[0].development_cards[0], [players[1]], Resource.Brick)
        assert Resource.Brick not in players[1].resources
        assert players[0].resources.count(Resource.Brick) == 3

    def test_create_game(self):
        game = Game()
        assert [player.name for player in game.players] == ["Alice", "Bob", "Charlie", "Dennis"]
        game.players[1].victory_points = 5
        game.players[3].victory_points = 3
        assert str(game) == "Bob: 5, Dennis: 3, Alice: 0, Charlie: 0"

TestClass().test_longest_road()