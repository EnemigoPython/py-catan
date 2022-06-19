import game

def game_resource_tests():
    tile = game.Tile("Hills", 3, [])
    assert tile.check_proc(5) is None
    assert isinstance(tile.check_proc(3), game.Resource)
    assert str(tile.check_proc(3)) == "Brick"

def main():
    game_resource_tests()

if __name__ == '__main__':
    main()
