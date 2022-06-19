import game

class TestClass:
    def test_game_resources(self):
        tile = game.Tile("Hills", 3, [])
        assert tile.check_proc(5) is None
        assert isinstance(tile.check_proc(3), game.Resource)
        assert str(tile.check_proc(3)) == "Brick"
        assert 3 == 5

