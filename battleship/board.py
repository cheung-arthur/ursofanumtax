import random

class Ship:
    def __init__(self, size, positions):
        self.size = size
        self.positions = positions
        self.hits = set()

    def register_hit(self, coord):
        if coord in self.positions:
            self.hits.add(coord)

    def is_sunk(self):
        return set(self.positions) == self.hits

class Board:
    def __init__(self, size=10):
        self.size = size
        self.ships = []
        self.guesses = set()
        self.generate_board()

    def generate_board(self):
        """Place ships of sizes 5, 4, 3, 3, 2 randomly."""
        ship_sizes = [5, 4, 3, 3, 2]
        for s in ship_sizes:
            ship_positions = self.place_ship_randomly(s)
            ship = Ship(s, ship_positions)
            self.ships.append(ship)

    def place_ship_randomly(self, ship_size):
        placed = False
        while not placed:
            orientation = random.choice(["horizontal", "vertical"])
            if orientation == "horizontal":
                row = random.randint(0, self.size - 1)
                col = random.randint(0, self.size - ship_size)
                new_positions = [(row, c) for c in range(col, col + ship_size)]
            else:
                row = random.randint(0, self.size - ship_size)
                col = random.randint(0, self.size - 1)
                new_positions = [(r, col) for r in range(row, row + ship_size)]

            # Check overlap
            overlap = any(pos in ship.positions for ship in self.ships for pos in new_positions)
            if not overlap:
                placed = True
                return new_positions

    def attack(self, coord):
        if coord in self.guesses:
            return "already guessed"
        self.guesses.add(coord)
        for ship in self.ships:
            if coord in ship.positions:
                ship.register_hit(coord)
                if ship.is_sunk():
                    return "hit and sunk"
                else:
                    return "hit"
        return "miss"

    def all_ships_sunk(self):
        return all(ship.is_sunk() for ship in self.ships)

    def get_layout(self):
        """
        Returns a list of ship position lists.
        Example: [ [(0,1),(0,2),(0,3),(0,4),(0,5)], [(3,3),(4,3),(5,3),(6,3)], ... ]
        """
        return [ship.positions for ship in self.ships]

    @classmethod
    def from_layout(cls, layout, size=10):
        """
        Creates a new Board with the same layout (i.e. same positions for each ship).
        """
        board = cls.__new__(cls)  # create an uninitialized instance
        board.size = size
        board.ships = []
        board.guesses = set()
        # No need to call generate_board(), since we're using the known layout
        for positions in layout:
            ship = Ship(len(positions), positions)
            board.ships.append(ship)
        return board
