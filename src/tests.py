import game

def main():
    tile = game.Tile("Hills", 3, [])
    assert tile.check_proc(5) is None
    assert tile.check_proc(3) == "Brick", tile.check_proc(3)

if __name__ == '__main__':
    main()