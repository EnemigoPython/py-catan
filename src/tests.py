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

    def test_construction_can_build(self):
        player = game.Player()
        player.resources.append(game.Resource.Brick)
        assert not game.Construction.can_build("Road", player)
        player.resources.append(game.Resource.Lumber)
        assert game.Construction.can_build("Road", player)
        player.resources = [
            game.Resource.Ore, 
            game.Resource.Ore, 
            game.Resource.Ore, 
            game.Resource.Grain,
            game.Resource.Grain 
        ]
        assert game.Construction.can_build("City", player)
        player.resources.pop()
        assert not game.Construction.can_build("City", player)
