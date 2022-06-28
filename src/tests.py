"""Tests to run via pytest"""
from game import *

class TestClass:
    def test_resources(self):
        tile = Tile("Hills", 3)
        assert tile.check_proc(5) is None
        assert tile.check_proc(3) is Resource.Brick

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
        assert str(player2.constructions[0]) == "Bob's Settlement"
        _ = Road(player1, tile, 0)
        assert len(player1.roads) == 1

    def test_create_board(self):
        board = Tile.create_board()
        assert len(board) == 5
        assert sum(len(l) for l in board) == 19
        assert str(board[0][0]) == "Mountains (10)"
        assert board[0][0].neighbours == [None, board[0][1], board[1][1], board[1][0], None, None]
        assert board[0][0].neighbours[1].neighbours[4] == board[0][0]
        assert board[0][1].neighbours == [None, board[0][2], board[1][2], board[1][1], board[0][0], None]
        assert [str(i) for i in board[1][3].neighbours] == [
            "None", 
            "None", 
            "Mountains (8)", 
            "Forest (3)", 
            "Pasture (4)", 
            "Forest (9)"
        ]
        assert [str(i) for i in board[1][1].neighbours] == [
            "Pasture (2)", 
            "Pasture (4)", 
            "Desert (0)", 
            "Forest (11)", 
            "Fields (12)", 
            "Mountains (10)"
        ]
        assert [i.number for i in board[2][2].neighbours] == [4, 3, 4, 3, 11, 6]
        assert [str(i) for i in board[3][0].neighbours] == [
            "Forest (11)", 
            "Mountains (3)", 
            "Hills (5)", 
            "None", 
            "None", 
            "Fields (9)"
        ]
        assert [i.number for i in board[3][2].neighbours] == [3, 5, 11, 6, 3, 0]
        assert [str(i) for i in board[3][3].neighbours] == [
            "Mountains (8)", 
            "None", 
            "None", 
            "Pasture (11)", 
            "Fields (4)", 
            "Forest (3)"
        ]
        assert [str(i) for i in board[4][0].neighbours] == [
            "Mountains (3)", 
            "Fields (6)", 
            "None", 
            "None", 
            "None", 
            "Forest (8)"
        ]
        assert [str(i) for i in board[4][2].neighbours] == [
            "Pasture (5)", 
            "None", 
            "None", 
            "None", 
            "Fields (6)", 
            "Fields (4)"
        ]

    def test_board_construction_multiple_tiles(self):
        board = Tile.create_board()
        player = Player("Alice")
        settlement = SettlementOrCity(player, board[0][0], 2)
        assert len(settlement.tiles) == 3
        assert all(tile in settlement.tiles for tile in (board[0][0], board[0][1], board[1][1]))
        assert board[0][1].construction_slots[4] is settlement
        assert board[1][1].construction_slots[0] is settlement
        settlement2 = SettlementOrCity(player, board[2][0], 4)
        assert len(settlement2.tiles) == 1
        assert settlement2.tiles[0] is board[2][0]
        settlement3 = SettlementOrCity(player, board[2][0], 0)
        assert len(settlement3.tiles) == 2
        assert board[1][0].construction_slots[4] is settlement3
        settlement4 = SettlementOrCity(player, board[4][0], 1)
        assert len(settlement4.tiles) == 3
        tile_numbers = [tile.number for tile in settlement4.tiles]
        assert all(num in tile_numbers for num in (3, 5, 6))
        assert len(player.constructions) == 4
        settlement5 = SettlementOrCity(player, board[2][4], 5)
        assert len(settlement5.tiles) == 3
        tile_names = [str(tile) for tile in settlement5.tiles]
        assert all(name in tile_names for name in ("Hills (10)", "Forest (3)", "Mountains (8)"))

    def test_harbours_on_created_board(self):
        board = Tile.create_board()
        assert sum(1 for _ in (harbour for layer in board for tile in layer for harbour in tile.harbour_slots 
            if isinstance(harbour, Harbour))) == 24 # uses of harbour (by multiple tiles)
        assert len(set(harbour for layer in board for tile in layer for harbour in tile.harbour_slots 
            if isinstance(harbour, Harbour))) == 9 # harbour instances
        assert len([slot for slot in board[0][0].harbour_slots if slot is not None]) == 2
        assert str(board[0][0].harbour_slots[0]) == "General Harbour"
        assert board[0][0].harbour_slots[0] is board[0][0].harbour_slots[5]
        assert str(board[0][2].harbour_slots[2]) == "Ore Harbour"
        assert board[0][2].harbour_slots[2] is board[1][3].harbour_slots[0]

    def test_player_owned_harbours(self):
        board = Tile.create_board()
        player = Player("Alice")
        assert len(player.harbours) == 0
        SettlementOrCity(player, board[0][0], 0)
        assert player.harbours[0].rate == 3
        SettlementOrCity(player, board[0][0], 4)
        assert len(player.harbours) == 1
        player2 = Player("Bob")
        SettlementOrCity(player2, board[0][2], 4)
        assert len(player2.harbours) == 0
        SettlementOrCity(player2, board[0][2], 2)
        assert player2.harbours[0].resource is Resource.Ore
        SettlementOrCity(player2, board[4][2], 1)
        assert len(player2.harbours) == 2
        resources = set(harbour.resource for harbour in player2.harbours)
        assert Resource.Wool in resources
        player3 = Player("Charlie")
        SettlementOrCity(player3, board[4][0], 1)
        SettlementOrCity(player2, board[4][0], 3)
        assert board[4][0].harbour_slots[3].rate == 3
        assert len(player3.harbours) == 0

    def test_player_init_position(self):
        board = Tile.create_board()
        player1 = Player("Alice")
        player1.init_position(board, [(0, 1, 2), (3, 2, 2)], [(0, 1, 2), (3, 2, 1)])
        assert len(player1.constructions) == 2
        assert len(player1.roads) == 2
        assert len(player1.harbours) == 0
        tile_types = set(tile.terrain for tile in player1.controlled_tiles)
        assert all(terrain in tile_types for terrain in ("Forest", "Fields", "Hills", "Mountains", "Pasture"))
        player2 = Player("Bob")
        player2.init_position(board, [(2, 1, 1), (1, 4, 0)], [(2, 1, 0), (1, 4, 0)])
        assert sum(1 for _ in (tile for tile in player2.controlled_tiles if tile.terrain == "Fields")) == 2
        assert sum(1 for _ in (tile for tile in player2.controlled_tiles if tile.number == 4)) == 2
        player3 = Player("Charlie")
        player3.init_position(board, [(3, 3, 3)], [])
        assert len(player3.constructions) == 1
        assert len(player3.roads) == 0
        assert len(player3.controlled_tiles) == 2
        assert len(player3.occupied_tiles) == 2
        assert len(player3.harbours) == 1
        player4 = Player("Dennis")
        try:
            player4.init_position(board, [(3, 3, 3)], [])
            raise Exception("Not allowed")
        except AssertionError:
            pass

    def test_mirrored_road_slot(self):
        board = Tile.create_board()
        player1 = Player("Alice")
        player1.init_position(board, [], [(0, 1, 2)])
        assert board[1][0].road_slots[2] is not None
        assert board[1][0].road_slots[2] is board[2][1].road_slots[5]
        assert len(player1.occupied_tiles) == 2
        assert len(player1.controlled_tiles) == 0
        SettlementOrCity(player1, board[1][0], 3)
        assert len(player1.occupied_tiles) == 3
        assert len(player1.controlled_tiles) == 3
        player2 = Player("Bob")
        player2.init_position(board, [], [(0, 0, 0)])
        assert len(player2.occupied_tiles) == 1
        player3 = Player("Charlie")
        player3.init_position(board, [], [(1, 0, 1)])
        try:
            Road(player3, board[0][2], 4)
            raise Exception("This is the mirrored position of the road we placed")
        except AssertionError:
            pass

    def test_adjacent_roads_detection(self):
        board = Tile.create_board()
        Player("Alice")
        player.init_position(board, [], [(1, 1, 5)])
        assert len(board[1][1].adjacent_roads(4)) == 1
        assert len(board[1][1].adjacent_roads(5)) == 0
        assert len(board[0][1].adjacent_roads(4)) == 1
        assert len(board[0][1].adjacent_roads(3)) == 1
        assert len(board[1][0].adjacent_roads(0)) == 1
        assert len(board[0][0].adjacent_roads(3)) == 1
        Player("Bob")
        player.init_position(board, [], [(2, 2, 5), (2, 1, 3)])
        assert len(board[2][2].adjacent_roads(5)) == 1
        assert len(board[1][1].adjacent_roads(2)) == 1
        assert len(board[1][2].adjacent_roads(4)) == 2
        Player("Charlie")
        player.init_position(board, [], [(1, 3, 0), (2, 3, 5), (1, 3, 2), (2, 3, 3), (2, 3, 4)])
        assert len(board[3][1].adjacent_roads(1)) == 4
        assert len(board[3][1].adjacent_roads(2)) == 2

    def test_adjacent_settlements_detection(self):
        board = Tile.create_board()
        player1 = Player("Alice")
        player1.init_position(board, [(1, 1, 4), (0, 0, 2)], [])
        assert len(board[1][0].adjacent_settlements(1)) == 2
        assert len(board[0][1].adjacent_settlements(3)) == 1
        assert len(board[1][1].adjacent_settlements(2)) == 0
        player2 = Player("Bob")
        player2.init_position(board, [(1, 2, 2)], [])
        assert len(board[2][1].adjacent_settlements(1)) == 2
        adjacent_settlements = [str(s) for s in board[2][1].adjacent_settlements(1)]
        assert all(s in adjacent_settlements for s in ("Alice's Settlement", "Bob's Settlement"))
        player3 = Player("Charlie")
        player3.init_position(board, [(1, 1, 2)], [])
        assert len(board[2][1].adjacent_settlements(1)) == 3
        adjacent_settlements = set(str(s) for s in board[2][1].adjacent_settlements(1))
        assert len(adjacent_settlements) == 3

    def test_build_road_method(self):
        board = Tile.create_board()
        player1 = Player("Alice")
        for _ in range(6):
            player1.resources.extend([
                Resource.Brick, 
                Resource.Lumber, 
            ])
        player1.init_position(board, [(0, 1, 2), (3, 2, 2)], [(3, 2, 1)])
        player1.build("Road", board[1][0], 3)
        player1.build("Road", board[1][0], 4)
        player1.build("Road", board[2][0], 1)
        player1.build("Road", board[2][4], 5)
        player1.build("Road", board[2][1], 3)
        try:
            player1.build("Road", board[2][4], 1)
            raise Exception("This road isn't connected to anything")
        except AssertionError:
            pass
        player2 = Player("Bob")
        player2.init_position(board, [(0, 4, 1)], [])
        player2.resources.extend([Resource.Brick, Resource.Lumber])
        try:
            player2.build("Road", board[2][4], 0)
            raise Exception("Bob doesn't own the adjacent road")
        except AssertionError:
            pass

    def test_build_settlement(self):
        board = Tile.create_board()
        player1 = Player("Alice")
        for _ in range(2):
            player1.resources.extend([
                Resource.Brick,
                Resource.Lumber,
                Resource.Wool,
                Resource.Grain
            ])
        player1.init_position(board, [(0, 1, 2), (3, 2, 2)], [(0, 1, 2), (0, 1, 3), (3, 2, 1)])
        player1.build("Settlement", board[1][0], 4)
        try:
            player1.build("Settlement", board[1][0], 3)
            raise Exception("This is too close to existing settlements")
        except AssertionError:
            pass
        player2 = Player("Bob")
        player2.init_position(board, [(0, 0, 1)], [(0, 0, 1), (1, 1, 0)])
        player2.resources.extend([
                Resource.Brick,
                Resource.Lumber,
                Resource.Wool,
                Resource.Grain
        ])
        player2.build("Settlement", board[1][1], 1)
        player3 = Player("Charlie")
        player3.init_position(board, [(2, 3, 3)], [(2, 3, 0), (2, 3, 1), (2, 3, 2)])
        for _ in range(2):
            player3.resources.extend([
                Resource.Brick,
                Resource.Lumber,
                Resource.Wool,
                Resource.Grain
            ])
        try:
            player3.build("Settlement", board[3][2], 1)
            raise Exception("Alice's settlement is too close")
        except AssertionError:
            pass
        player3.build("Settlement", board[3][2], 0)
        try:
            player3.build("Settlement", board[4][2], 4)
            raise Exception("There are no roads connecting this point")
        except AssertionError:
            pass
