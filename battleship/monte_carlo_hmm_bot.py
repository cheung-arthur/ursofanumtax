# file: battleship/monte_carlo_hmm_bot.py

import random
from battleship.hmm import BattleshipHMM

class MonteCarloHMMBot:
    """
    A Battleship bot that:
      - Maintains a local grid of known hits/misses/sunk squares.
      - Uses BattleshipHMM to track a distribution over possible layouts.
      - Each turn, it updates the HMM (forward pass), prunes states,
        and picks the cell with highest marginal probability.
    """

    def __init__(self, board_size=10, sample_count=2000):
        self.board_size = board_size
        self.sample_count = sample_count

        # Our local knowledge of the board
        self.grid = [['.' for _ in range(board_size)] for _ in range(board_size)]
        self.unknown_cells = [(r,c) for r in range(board_size) for c in range(board_size)]

        # Initialize the HMM
        self.hmm = BattleshipHMM(board_size=board_size, sample_count=sample_count)

    def update_knowledge(self, coord, result):
        """
        Called after each guess to incorporate new info into self.grid + HMM
        """
        r, c = coord
        if (r,c) in self.unknown_cells:
            self.unknown_cells.remove((r,c))

        if result == "miss":
            self.grid[r][c] = 'M'
        elif result == "hit":
            self.grid[r][c] = 'H'
        elif result == "hit and sunk":
            self.grid[r][c] = 'S'
            self._mark_sunk_group(coord)

        # We call the HMM forward update with the new observation
        obs = (coord, result)
        self.hmm.forward(obs, self.grid)

    def choose_move(self):
        """
        Pick the unknown cell with highest probability of containing a ship,
        as computed by the HMM's marginal distribution.
        """
        if not self.unknown_cells:
            return None

        # If distribution is empty, fallback to random
        if not self.hmm.states:
            return random.choice(self.unknown_cells)

        # Get marginal probabilities
        cell_probs = self.hmm.get_marginal_cell_probs()

        best_val = -1.0
        best_cells = []
        for (r,c) in self.unknown_cells:
            if cell_probs[r][c] > best_val:
                best_val = cell_probs[r][c]
                best_cells = [(r,c)]
            elif abs(cell_probs[r][c] - best_val) < 1e-9:
                best_cells.append((r,c))

        return random.choice(best_cells) if best_cells else None

    def _mark_sunk_group(self, start):
        """
        If we get 'hit and sunk' at start, mark contiguous 'H' squares as 'S'.
        """
        stack = [start]
        while stack:
            r,c = stack.pop()
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                    if self.grid[nr][nc] == 'H':
                        self.grid[nr][nc] = 'S'
                        stack.append((nr,nc))
