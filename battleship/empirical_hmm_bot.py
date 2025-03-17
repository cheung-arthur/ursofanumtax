import random
import pandas as pd
import numpy as np
from battleship.hmm import BattleshipHMM

class EmpiricalHMMBot:
    """
    A Battleship bot that uses:
      1) A Hidden Markov Model (BattleshipHMM),
      2) An "empirical" usage heatmap from data/battleship_game_squares.csv,
    to pick moves with a hybrid approach.

    Workflow each turn:
      - Update the HMM with the latest observation.
      - Get marginal cell probabilities from the HMM.
      - Multiply by the empirical usage frequencies for each cell
        to get a final "weighted" probability map.
      - Choose the unknown cell with the highest weighted probability.
    """

    def __init__(self, board_size=10, sample_count=2000,
                 csv_path="data/battleship_game_squares.csv"):
        self.board_size = board_size
        self.sample_count = sample_count
        self.csv_path = csv_path

        # Our local board knowledge:
        # '.'=unknown, 'M'=miss, 'H'=hit, 'S'=sunk
        self.grid = [['.' for _ in range(board_size)] for _ in range(board_size)]
        self.unknown_cells = [(r,c) for r in range(board_size) for c in range(board_size)]

        # Create the HMM
        self.hmm = BattleshipHMM(board_size=board_size, sample_count=sample_count)

        # Load the empirical usage frequencies
        self.empirical = self._load_empirical_data()

    def update_knowledge(self, coord, result):
        """
        Called after each guess with the outcome: 'miss', 'hit',
        or 'hit and sunk'.
        Update local knowledge & reweight HMM.
        """
        r, c = coord
        if coord in self.unknown_cells:
            self.unknown_cells.remove(coord)

        if result == "miss":
            self.grid[r][c] = 'M'
        elif result == "hit":
            self.grid[r][c] = 'H'
        elif result == "hit and sunk":
            self.grid[r][c] = 'S'
            self._mark_sunk_group(coord)

        # Update HMM with new observation
        self.hmm.forward((coord, result), self.grid)

    def choose_move(self):
        """
        Use a hybrid approach:
          - If HMM distribution is empty, pick randomly.
          - Otherwise, combine HMM marginal cell probabilities with
            empirical frequencies, and pick the highest combined score.
        """
        if not self.unknown_cells:
            return None  # No moves left

        # If we have no valid HMM states, fallback to random
        if not self.hmm.states:
            return random.choice(self.unknown_cells)

        # 1) Get standard HMM marginal probabilities
        hmm_probs = self.hmm.get_marginal_cell_probs()

        # 2) Combine with empirical usage
        best_score = -1.0
        best_cells = []
        for (r,c) in self.unknown_cells:
            # Score = HMM probability * empirical frequency
            # (Add a tiny constant to avoid zero if empirical is 0)
            score = hmm_probs[r][c] * (self.empirical[r][c] + 1e-9)
            if score > best_score:
                best_score = score
                best_cells = [(r,c)]
            elif abs(score - best_score) < 1e-12:
                best_cells.append((r,c))

        # If everything is zero, fallback randomly
        if not best_cells:
            return random.choice(self.unknown_cells)

        # Tie-break among top-scoring cells
        return random.choice(best_cells)

    # ----------------------------------------------------------------------
    # Internal helpers
    # ----------------------------------------------------------------------
    def _load_empirical_data(self):
        """
        Loads the CSV from ../data/battleship_game_squares.csv,
        sums 'games' by square, reshapes into a 10x10 array,
        then flips rows so row 0 => 'A' at top.
        """
        df = pd.read_csv(self.csv_path)

        # Sum 'games' by square
        square_games = df.groupby("square")["games"].sum().reset_index()

        # Build the 10x10 matrix
        data_array = np.zeros((self.board_size, self.board_size))
        for _, row in square_games.iterrows():
            square_id = row["square"] - 1  # 0-based
            rr, cc = divmod(square_id, self.board_size)
            data_array[rr, cc] = row["games"]

        # Flip vertically so that row=0 is "A" at the top (like in exploration)
        data_array = np.flipud(data_array)

        return data_array

    def _mark_sunk_group(self, start):
        """
        Mark contiguous 'H' cells as 'S' if we get 'hit and sunk' at start.
        """
        stack = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                    if self.grid[nr][nc] == 'H':
                        self.grid[nr][nc] = 'S'
                        stack.append((nr,nc))
