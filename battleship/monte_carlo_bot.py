import random
import time

class MonteCarloBot:
    def __init__(self, board_size=10, simulation_iterations=10000):
        self.board_size = board_size
        # '.' = unknown, 'M' = miss, 'H' = hit, 'S' = sunk.
        self.grid = [['.' for _ in range(board_size)] for _ in range(board_size)]
        self.remaining_ships = [5, 4, 3, 3, 2]
        self.simulation_iterations = simulation_iterations

    def update_knowledge(self, coord, result):
        r, c = coord
        if result == "miss":
            self.grid[r][c] = 'M'
        elif result == "hit":
            self.grid[r][c] = 'H'
        elif result == "hit and sunk":
            self.grid[r][c] = 'H'
            ship_size = self.infer_sunk_ship_size(coord)
            if ship_size in self.remaining_ships:
                self.remaining_ships.remove(ship_size)
            self.mark_sunk_ship(coord)

    def infer_sunk_ship_size(self, coord):
        visited = set()
        def dfs(r, c):
            if (r, c) in visited:
                return 0
            if r < 0 or r >= self.board_size or c < 0 or c >= self.board_size:
                return 0
            if self.grid[r][c] != 'H':
                return 0
            visited.add((r, c))
            return (1 + dfs(r+1, c) + dfs(r-1, c)
                      + dfs(r, c+1) + dfs(r, c-1))

        size = dfs(*coord)
        # If only a single cell is hit, default to 2 (edge case).
        return size if size > 1 else 2

    def mark_sunk_ship(self, coord):
        stack = [coord]
        visited = set()
        while stack:
            r, c = stack.pop()
            if (r, c) in visited:
                continue
            visited.add((r, c))
            if self.grid[r][c] == 'H':
                self.grid[r][c] = 'S'
                for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                        if self.grid[nr][nc] == 'H':
                            stack.append((nr, nc))

    def get_possible_placements(self, ship_size):
        placements = []
        n = self.board_size
        # Horizontal
        for r in range(n):
            for c in range(n - ship_size + 1):
                placement = [(r, c+i) for i in range(ship_size)]
                if self.is_placement_valid(placement):
                    placements.append(placement)
        # Vertical
        for c in range(n):
            for r in range(n - ship_size + 1):
                placement = [(r+i, c) for i in range(ship_size)]
                if self.is_placement_valid(placement):
                    placements.append(placement)
        return placements

    def is_placement_valid(self, placement):
        for (r, c) in placement:
            # 'M' => definitely no ship here
            if self.grid[r][c] == 'M':
                return False
            # If 'S', that’s already a sunk ship segment
            # so no other ship can be there
            if self.grid[r][c] == 'S':
                return False
        return True

    def run_simulation(self, time_limit=3.0):
        n = self.board_size
        square_frequencies = [[0 for _ in range(n)] for _ in range(n)]
        valid_configurations = 0

        # Precompute possible placements
        possible_placements_for_ship = {}
        for ship_size in self.remaining_ships:
            placements = self.get_possible_placements(ship_size)
            possible_placements_for_ship[ship_size] = placements

        start_time = time.time()
        iterations = 0

        while time.time() - start_time < time_limit:
            iterations += 1
            configuration = []
            used_cells = set()
            valid_configuration = True

            for ship_size in self.remaining_ships:
                placements = possible_placements_for_ship.get(ship_size, [])
                if not placements:
                    valid_configuration = False
                    break
                valid_placements = [
                    p for p in placements
                    if not any(cell in used_cells for cell in p)
                ]
                if not valid_placements:
                    valid_configuration = False
                    break
                chosen = random.choice(valid_placements)
                configuration.append(chosen)
                used_cells.update(chosen)

            if not valid_configuration:
                continue

            # Ensure all 'H' cells are covered by at least one chosen ship
            hits_required = [
                (r, c) for r in range(n) for c in range(n)
                if self.grid[r][c] == 'H'
            ]
            if not all(
                any(hit in ship for ship in configuration)
                for hit in hits_required
            ):
                continue

            # If it passes, count it and update frequencies
            valid_configurations += 1
            for ship in configuration:
                for (r, c) in ship:
                    square_frequencies[r][c] += 1

        # Normalize
        if valid_configurations > 0:
            for r in range(n):
                for c in range(n):
                    square_frequencies[r][c] /= valid_configurations

        return square_frequencies, valid_configurations, iterations

    def choose_move(self, time_limit=3.0):
        frequencies, valid_configs, iterations = self.run_simulation(time_limit=time_limit)
        n = self.board_size
        best_freq = -1
        best_moves = []

        for r in range(n):
            for c in range(n):
                if self.grid[r][c] == '.':
                    if frequencies[r][c] > best_freq:
                        best_freq = frequencies[r][c]
                        best_moves = [(r, c)]
                    elif frequencies[r][c] == best_freq:
                        best_moves.append((r, c))

        # Now call display_heatmap
        self.display_heatmap(frequencies, best_moves, valid_configs, iterations)
        if best_moves:
            # For example, choose randomly among the top squares:
            return random.choice(best_moves)
        else:
            # No unknown cells left
            return None

    def display_heatmap(self, frequencies, best_moves, valid_configs, iterations):
        """
        Display a terminal heat map of probabilities.
        """
        print("Heatmap of probabilities:")
        n = self.board_size
        header = "   " + " ".join([chr(ord('A') + c) for c in range(n)])
        print(header)
        for r in range(n):
            row_str = f"{r+1:2} "
            for c in range(n):
                val = frequencies[r][c]
                cell_str = f"{val:.2f}"
                if (r, c) in best_moves:
                    # highlight best moves
                    cell_str = "[" + cell_str + "]"
                else:
                    cell_str = " " + cell_str + " "
                row_str += cell_str
            print(row_str)
        print(f"Valid configurations: {valid_configs}, Iterations: {iterations}")
