import random

class MonteCarloHeuristicsBot:
    def __init__(self, board_size=10, iterations=1000):
        self.board_size = board_size
        self.iterations = iterations
        # Grid: '.' for unknown, 'M' for miss, 'H' for hit (unsunk), 'S' for sunk.
        self.grid = [['.' for _ in range(board_size)] for _ in range(board_size)]
        self.unknown_cells = [(r, c) for r in range(board_size) for c in range(board_size)]
        # The standard Battleship ships: sizes 5, 4, 3, 3, and 2.
        self.remaining_ship_sizes = [5, 4, 3, 3, 2]

    def update_knowledge(self, coord, result):
        r, c = coord
        if coord in self.unknown_cells:
            self.unknown_cells.remove(coord)
        if result == "miss":
            self.grid[r][c] = 'M'
        elif result == "hit":
            self.grid[r][c] = 'H'
        elif result == "hit and sunk":
            # Mark this cell as sunk and update any contiguous hit cells as sunk.
            self.grid[r][c] = 'S'
            sunk_cells = self._get_sunk_group(coord)
            ship_size = len(sunk_cells)
            # Remove one occurrence of the ship size that was sunk.
            if ship_size in self.remaining_ship_sizes:
                self.remaining_ship_sizes.remove(ship_size)

    def choose_move(self):
        # If no remaining ships, fall back to a random unknown cell.
        if not self.remaining_ship_sizes:
            print("UNKNOWN PROBS, IMMA CHOOSE RANDOM")
            return random.choice(self.unknown_cells) if self.unknown_cells else None

        # Build a probability map (2D array) for each board cell.
        prob = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        valid_configurations = 0

        # Work with the remaining ship sizes in descending order.
        ship_sizes = sorted(self.remaining_ship_sizes, reverse=True)

        # Precompute candidate placements for each ship size.
        candidate_options = {}
        for s in ship_sizes:
            candidate_options[s] = self._get_candidate_placements(s)

        # Monte Carlo iterations: try to build a complete configuration.
        for _ in range(self.iterations):
            configuration = []
            used = set()  # Cells already occupied by a placed ship.
            valid = True
            for s in ship_sizes:
                valid_candidates = [
                    placement for placement in candidate_options[s]
                    if not set(placement) & used
                ]
                if not valid_candidates:
                    valid = False
                    break
                placement = random.choice(valid_candidates)
                configuration.append(placement)
                used.update(placement)
            if not valid:
                continue
            # Check that every known "hit" (unsunk) is covered by at least one ship in this configuration.
            if not self._configuration_covers_hits(configuration):
                continue

            # Valid configuration – add its contributions to the probability map.
            valid_configurations += 1
            for placement in configuration:
                for (r, c) in placement:
                    prob[r][c] += 1

        # If no valid configuration was found, fall back to a random unknown cell.
        if valid_configurations == 0:
            return random.choice(self.unknown_cells) if self.unknown_cells else None

        # Normalize the heatmap.
        normalized_heatmap = [
            [prob[r][c] / valid_configurations for c in range(self.board_size)]
            for r in range(self.board_size)
        ]
        # Print the heatmap to the terminal.
        self.print_heatmap(normalized_heatmap)

        # Choose the unknown cell with the highest probability.
        best_prob = -1
        best_cells = []
        for (r, c) in self.unknown_cells:
            cell_prob = normalized_heatmap[r][c]
            if cell_prob > best_prob:
                best_prob = cell_prob
                best_cells = [(r, c)]
            elif cell_prob == best_prob:
                best_cells.append((r, c))
            
        return random.choice(best_cells) if best_cells else None

    def print_heatmap(self, heatmap):
        """Prints the heatmap as a grid of normalized probabilities."""
        print("Heatmap:")
        # Print column headers
        header = "    " + " ".join(f"{chr(ord('A') + c):>5}" for c in range(self.board_size))
        print(header)
        for r, row in enumerate(heatmap):
            # Format each cell's probability to two decimal places.
            row_str = " ".join(f"{cell:5.2f}" for cell in row)
            print(f"{r+1:2}  {row_str}")
        print()  # extra newline for readability

    def _get_candidate_placements(self, ship_size):
        """
        Generate all candidate placements for a ship of a given size that do not conflict with
        known misses or sunk cells.
        """
        placements = []
        for r in range(self.board_size):
            for c in range(self.board_size):
                # Horizontal placement.
                if c + ship_size <= self.board_size:
                    placement = [(r, c + i) for i in range(ship_size)]
                    if self._placement_is_valid(placement):
                        placements.append(placement)
                # Vertical placement.
                if r + ship_size <= self.board_size:
                    placement = [(r + i, c) for i in range(ship_size)]
                    if self._placement_is_valid(placement):
                        placements.append(placement)
        return placements

    def _placement_is_valid(self, placement):
        """
        A placement is valid if none of its cells conflict with known misses ('M') or sunk cells ('S').
        Hits ('H') and unknown cells ('.') are allowed.
        """
        for (r, c) in placement:
            if self.grid[r][c] in ['M', 'S']:
                return False
        return True

    def _configuration_covers_hits(self, configuration):
        """
        Check that every cell in the grid marked as a 'H' (hit) is covered by at least one ship
        in the current configuration.
        """
        covered = set()
        for placement in configuration:
            covered.update(placement)
        for r in range(self.board_size):
            for c in range(self.board_size):
                if self.grid[r][c] == 'H' and (r, c) not in covered:
                    return False
        return True

    def _get_sunk_group(self, coord):
        """
        Given a coordinate that just received a "hit and sunk" result, perform a DFS to collect
        all contiguous cells that are marked as hit ('H') or sunk ('S'). Also, mark all these cells
        as sunk ('S').
        """
        stack = [coord]
        group = set()
        while stack:
            cell = stack.pop()
            if cell in group:
                continue
            r, c = cell
            if self.grid[r][c] in ['H', 'S']:
                group.add(cell)
                # Mark as sunk.
                self.grid[r][c] = 'S'
                # Check neighbors (up, down, left, right).
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                        if self.grid[nr][nc] in ['H', 'S'] and (nr, nc) not in group:
                            stack.append((nr, nc))
        return group
