import random

class RandomBot:

    def __init__(self, board_size=10):
        self.board_size = board_size
        # '.' = unknown, 'M' = miss, 'H' = hit, 'S' = sunk.
        self.grid = [['.' for _ in range(board_size)] for _ in range(board_size)]
        # Keep track of all cells not yet guessed.
        self.unknown_cells = [(r, c) for r in range(board_size) for c in range(board_size)]

    def update_knowledge(self, coord, result):
        r, c = coord
        # Remove this cell from unknown cells (so we don't guess it again).
        if coord in self.unknown_cells:
            self.unknown_cells.remove(coord)

        if result == "miss":
            self.grid[r][c] = 'M'
        elif result == "hit":
            self.grid[r][c] = 'H'
        elif result == "hit and sunk":
            # We won't bother deducing which ship or its entire location.
            self.grid[r][c] = 'H'

    def choose_move(self):
        if not self.unknown_cells:
            return None
        return random.choice(self.unknown_cells)
