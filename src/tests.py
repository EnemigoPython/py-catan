"""Tests to run via pytest"""
import game

class TestClass:
    def test_resources(self):
        tile = game.Tile("Hills", 3)
        assert tile.check_proc(5) is None
        assert tile.check_proc(3) is game.Resource.Brick

    def test_construction(self):
        road = game.Construction("Road", owner=game.Player())
        assert str(road) == "Default's Road"
        try:
            game.Construction("Invalid", owner=game.Player())
            raise Exception("This should not be ok")
        except AssertionError:
            pass

    def test_construction_has_resources(self):
        player = game.Player()
        player.resources.append(game.Resource.Brick)
        assert not game.Construction.has_resources(player, "Road")
        player.resources.append(game.Resource.Lumber)
        assert game.Construction.has_resources(player, "Road")
        player.resources = [
            game.Resource.Ore, 
            game.Resource.Ore, 
            game.Resource.Ore, 
            game.Resource.Grain,
            game.Resource.Grain 
        ]
        assert game.Construction.has_resources(player, "City")
        player.resources.pop()
        assert not game.Construction.has_resources(player, "City")
        assert not game.Construction.has_resources(player, "Development Card")

    def test_construction_slot(self):
        tile = game.Tile("Hills", 3)
        settlement1 = game.SettlementOrCity(game.Player(), tile, 0)
        assert tile.construction_slots[0] is settlement1
        assert tile.construction_slots[1] is None
        settlement2 = game.SettlementOrCity(game.Player(), tile, 1)
        assert tile.construction_slots[1] is settlement2
        try:
            _ = game.SettlementOrCity(game.Player(), tile, 1)
            Exception("Not allowed to build on a used slot")
        except AssertionError:
            pass
        try:
            _ = game.SettlementOrCity(game.Player(), tile, 6)
            Exception("Also not allowed to build on invalid index")
        except AssertionError:
            pass
        road = game.Road(game.Player(), tile, 1)
        assert tile.road_slots[1] is road


    def test_player_controlled_construction(self):
        player1 = game.Player(name="Alice")
        tile = game.Tile("Hills", 3)
        _ = game.SettlementOrCity(player1, tile, 0)
        print(player1.occupied_tiles)
        assert len(player1.constructions) == 1
        _ = game.SettlementOrCity(player1, tile, 1)
        assert len(player1.constructions) == 2
        player2 = game.Player(name="Bob")
        _ = game.SettlementOrCity(player2, tile, 2)
        assert len(player1.constructions) == 2
        assert str(player2.constructions[0]) == "Bob's Settlement"
        _ = game.Road(player1, tile, 0)
        assert len(player1.roads) == 1

    def test_create_board(self):
        board = game.Tile.create_board()
        assert len(board) == 5
        assert sum(len(l) for l in board) == 19
        assert str(board[0][0]) == "Mountains"
        assert board[0][0].neighbours == [None, board[0][1], board[1][1], board[1][0], None, None]
        assert board[0][0].neighbours[1].neighbours[4] == board[0][0]
        assert board[0][1].neighbours == [None, board[0][2], board[1][2], board[1][1], board[0][0], None]
        assert [str(i) for i in board[1][3].neighbours] == ["None", "None", "Mountains", "Forest", "Pasture", "Forest"]
        assert [str(i) for i in board[1][1].neighbours] == ["Pasture", "Pasture", "Desert", "Forest", "Fields", "Mountains"]
        assert [i.number for i in board[2][2].neighbours] == [4, 3, 4, 3, 11, 6]
        assert [str(i) for i in board[3][0].neighbours] == ["Forest", "Mountains", "Hills", "None", "None", "Fields"]
        assert [i.number for i in board[3][2].neighbours] == [3, 5, 11, 6, 3, 0]
        assert [str(i) for i in board[3][3].neighbours] == ["Mountains", "None", "None", "Pasture", "Fields", "Forest"]
        assert [str(i) for i in board[3][3].neighbours] == ["Mountains", "None", "None", "Pasture", "Fields", "Forest"]
        assert [str(i) for i in board[4][0].neighbours] == ["Mountains", "Fields", "None", "None", "None", "Forest"]
        assert [str(i) for i in board[4][2].neighbours] == ["Pasture", "None", "None", "None", "Fields", "Fields"]

    def test_board_construction_multiple_tiles(self):
        board = game.Tile.create_board()
        player = game.Player("Alice")
        settlement = game.SettlementOrCity(player, board[0][0], 2)
        assert len(settlement.tiles) == 3
        assert all(tile in settlement.tiles for tile in (board[0][0], board[0][1], board[1][1]))
        assert board[0][1].construction_slots[4] is settlement
        assert board[1][1].construction_slots[0] is settlement
        settlement2 = game.SettlementOrCity(player, board[2][0], 4)
        assert len(settlement2.tiles) == 1
        assert settlement2.tiles[0] is board[2][0]
        settlement3 = game.SettlementOrCity(player, board[2][0], 0)
        assert len(settlement3.tiles) == 2
        assert board[1][0].construction_slots[4] is settlement3
        settlement4 = game.SettlementOrCity(player, board[4][0], 1)
        assert len(settlement4.tiles) == 3
        tile_numbers = [tile.number for tile in settlement4.tiles]
        assert all(num in tile_numbers for num in (3, 5, 6))
        assert len(player.constructions) == 4
        settlement5 = game.SettlementOrCity(player, board[2][4], 5)
        assert len(settlement5.tiles) == 3
        tile_names = [str(tile) for tile in settlement5.tiles]
        assert all(name in tile_names for name in ("Hills", "Forest", "Mountains"))
