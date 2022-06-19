class InvalidResourceException(Exception):
    """Custom error handler for creation of unidentified resource"""

class Resource:
    def __init__(self, name):
        if name in ("Brick", "Lumber", "Ore", "Grain", "Wool"):
            self.name = name
        else:
            raise InvalidResourceException(f"{name} is not a resource")

    def __str__(self):
        return self.name

class Tile:
    """A single tile on the Catan game board"""
    resource_dict = {
        "Desert": None,
        "Hills": Resource("Brick"),
        "Forest": Resource("Lumber"),
        "Mountains": Resource("Ore"),
        "Fields": Resource("Grain"),
        "Pasture": Resource("Wool")
    }
    
    def __init__(self, terrain, number, neighbours):
        self.terrain = terrain
        self.number = number
        self.neighbours = neighbours
        self.resource = self.resource_dict[self.terrain]

    def check_proc(self, number):
        if self.number == number:
            return self.resource_dict[self.terrain]
        return None

class Construction:
    """An item constructed by a player"""
    pass

# x = Resource("hi")