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

    def test_construction_can_build(self):
        player = game.Player()
        player.resources.append(game.Resource.Brick)
        assert not game.Construction.can_build(player, "Road")
        player.resources.append(game.Resource.Lumber)
        assert game.Construction.can_build(player, "Road")
        player.resources = [
            game.Resource.Ore, 
            game.Resource.Ore, 
            game.Resource.Ore, 
            game.Resource.Grain,
            game.Resource.Grain 
        ]
        assert game.Construction.can_build(player, "City")
        player.resources.pop()
        assert not game.Construction.can_build(player, "City")
        assert not game.Construction.can_build(player, "Development Card")

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
        assert len(player1.constructions) == 1
        _ = game.SettlementOrCity(player1, tile, 1)
        assert len(player1.constructions) == 2
        player2 = game.Player(name="Bob")
        _ = game.SettlementOrCity(player2, tile, 2)
        assert len(player1.constructions) == 2
        assert str(player2.constructions[0]) == "Bob's Settlement"
        _ = game.Road(player1, tile, 0)
        assert len(player1.roads) == 1

    def test_connected_tile_construction(self):
        connected_tiles = [
            game.Tile("Desert", 0)
        ]
