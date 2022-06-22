import game

class TestClass:
    def test_resources(self):
        tile = game.Tile("Hills", 3, [])
        assert tile.check_proc(5) is None
        assert tile.check_proc(3) is game.Resource.Brick

    def test_construction(self):
        road = game.Construction("Road")
        assert str(road) == "Road"
        try:
            game.Construction("Invalid")
            raise Exception("This should not be ok")
        except AssertionError:
            pass
