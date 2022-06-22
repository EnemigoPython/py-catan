import game

class TestClass:
    def test_game_resources(self):
        tile = game.Tile("Hills", 3, [])
        assert tile.check_proc(5) is None
        assert tile.check_proc(3) is game.Resource.Brick
