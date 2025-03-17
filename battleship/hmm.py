import random

class BattleshipHMM:
    """
    A simplified particle-filter-based HMM for Battleship.
    Each state = one possible placement of ships.
    Observations = (coord, result) e.g. ( (r,c), 'miss'/'hit'/'hit and sunk' ).
    
    Key Methods:
      - build_initial_distribution(known_grid): 
          sample a set of consistent states from scratch
      - forward(observation, known_grid):
          re-weight states by P(observation | state), prune invalid
          states, then resample to maintain a constant population
      - backward(...):
          placeholder for backward pass if we had a full observation sequence
      - viterbi(...):
          placeholder if we want the single best sequence or single best state
      - get_marginal_cell_probs():
          for each cell, sum of (weights of states containing that cell)
    """

    def __init__(self, board_size=10, ship_sizes=None, sample_count=500):
        self.board_size = board_size
        if ship_sizes is None:
            ship_sizes = [5,4,3,3,2]
        self.ship_sizes = sorted(ship_sizes, reverse=True)  # largest first
        self.sample_count = sample_count

        # A list of states (ship layouts), each layout = tuple of ships
        # A parallel list of weights
        self.states = []
        self.weights = []

        # We track whether we have built an initial distribution
        self.initialized = False

    ###########################################################################
    # Public interface
    ###########################################################################

    def build_initial_distribution(self, known_grid):
        """
        Build a set of sample_count states that match the known grid 
        (cover 'H' squares, exclude 'M' squares, etc.).
        """
        self.states = []
        self.weights = []

        # We'll do multiple attempts to place ships randomly
        attempts = 0
        max_attempts = self.sample_count * 20
        while len(self.states) < self.sample_count and attempts < max_attempts:
            layout = self._sample_layout(known_grid)
            attempts += 1
            if layout is not None:
                self.states.append(layout)
                self.weights.append(1.0)  # uniform

        if not self.states:
            # none found, distribution is empty
            return
        
        # normalize
        total = sum(self.weights)
        for i in range(len(self.weights)):
            self.weights[i] /= total

        self.initialized = True

    def forward(self, observation, known_grid):
        """
        Incorporate a new observation by re-weighting states:
          weight[state] *= P(observation | state)
        Then prune impossible states and resample.

        observation is typically a tuple: ( (r,c), resultString )
        known_grid used to do logic-based pruning (miss => no ship, etc.).
        """
        if not self.initialized:
            # If no initial distribution, build from scratch
            self.build_initial_distribution(known_grid)
            return

        if not self.states:
            # empty distribution => no update
            return

        coord, result = observation
        new_weights = []
        for s, w in zip(self.states, self.weights):
            like = self._likelihood_of_observation(s, coord, result)
            new_w = w * like
            new_weights.append(new_w)
        
        total = sum(new_weights)
        if total < 1e-15:
            # Everything died out
            self.states = []
            self.weights = []
            return

        for i in range(len(new_weights)):
            new_weights[i] /= total

        # Resample
        self.states, self.weights = self._resample(self.states, new_weights, self.sample_count)

        # Additional logic pruning with known_grid
        self._prune_inconsistent(known_grid)

    def backward(self, observations):
        """
        Placeholder for a backward pass if we had a full sequence of observations.
        Typically not used interactively since we only get observations step by step.
        """
        # For a static layout, there's no typical transition from time t to t+1, 
        # so a full forward-backward algorithm might be trivial. 
        # You could do offline analysis if you had all moves at once.
        pass

    def viterbi(self):
        """
        Return the single most probable state (layout) in the distribution.
        """
        if not self.states:
            return None
        # argmax
        max_idx = max(range(len(self.states)), key=lambda i: self.weights[i])
        return self.states[max_idx]

    def get_marginal_cell_probs(self):
        """
        For each cell, sum up the weights of the states that contain that cell.
        Return a 2D list (board_size x board_size).
        """
        cell_probs = [[0.0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        for layout, w in zip(self.states, self.weights):
            # flatten
            all_cells = set()
            for ship_positions in layout:
                all_cells.update(ship_positions)
            for (r,c) in all_cells:
                cell_probs[r][c] += w
        return cell_probs

    ###########################################################################
    # Internal / Private Methods
    ###########################################################################

    def _sample_layout(self, known_grid):
        """
        Attempt to place all ships to get a single random layout that matches known_grid,
        covering all 'H' squares, excluding 'M' squares, etc.
        Return a tuple of ships, each ship = tuple of coords, or None if fail.
        """
        used = set()
        layout = []
        for size in self.ship_sizes:
            placement = self._random_ship_placement(size, used, known_grid)
            if not placement:
                return None
            layout.append(tuple(sorted(placement)))
            used.update(placement)

        # Check it covers all 'H' squares
        if not self._covers_all_hits(layout, known_grid):
            return None

        # Sort final layout for consistency
        layout = tuple(sorted(layout))
        return layout

    def _random_ship_placement(self, ship_size, used, grid):
        """
        Randomly place a ship of length ship_size ignoring overlaps and squares 
        that conflict with 'M' or 'S' (unless you want more advanced logic for 'S').
        """
        candidates = []
        for r in range(self.board_size):
            for c in range(self.board_size):
                # horizontal
                if c + ship_size <= self.board_size:
                    coords = [(r,c+i) for i in range(ship_size)]
                    if self._valid_placement(coords, used, grid):
                        candidates.append(coords)
                # vertical
                if r + ship_size <= self.board_size:
                    coords = [(r+i,c) for i in range(ship_size)]
                    if self._valid_placement(coords, used, grid):
                        candidates.append(coords)

        if not candidates:
            return None

        return random.choice(candidates)

    def _valid_placement(self, coords, used, grid):
        """ 
        Valid if it doesn't overlap 'used', 
        and doesn't place a ship in 'M' squares, 
        or an 'S' square that doesn't match the logic 
        (we do the simpler approach: no new ship can cross an 'S' cell).
        """
        for (r,c) in coords:
            if (r,c) in used:
                return False
            if grid[r][c] == 'M':
                return False
            if grid[r][c] == 'S':
                return False
        return True

    def _covers_all_hits(self, layout, grid):
        """All 'H' squares must be in at least one ship of layout."""
        all_cells = set()
        for ship_positions in layout:
            all_cells.update(ship_positions)
        for r in range(self.board_size):
            for c in range(self.board_size):
                if grid[r][c] == 'H':
                    if (r,c) not in all_cells:
                        return False
        return True

    def _likelihood_of_observation(self, layout, coord, result):
        """
        Return a simple 1 if layout is consistent with observation at coord, else 0.
        This is the forward update: P(obs|state).
        """
        all_cells = set()
        for ship_positions in layout:
            all_cells.update(ship_positions)

        (r,c) = coord
        if result == "miss":
            return 0.0 if (r,c) in all_cells else 1.0
        if result.startswith("hit"):
            return 1.0 if (r,c) in all_cells else 0.0
        # e.g. "already guessed" => do nothing
        return 1.0

    def _prune_inconsistent(self, grid):
        """
        Remove states that conflict with the known grid 
        (e.g. 'M' => no ship; 'H' => must have ship; 'S' => must have ship).
        Then normalize & possibly resample again.
        """
        keep_states = []
        keep_weights = []
        for s, w in zip(self.states, self.weights):
            if not self._conflicts_with_grid(s, grid):
                keep_states.append(s)
                keep_weights.append(w)

        total = sum(keep_weights)
        if total < 1e-15:
            self.states = []
            self.weights = []
            return

        for i in range(len(keep_weights)):
            keep_weights[i] /= total

        # Optionally do a second resampling
        self.states, self.weights = self._resample(keep_states, keep_weights, self.sample_count)

    def _conflicts_with_grid(self, layout, grid):
        """Basic logic: 'M' => cannot have ship, 'H' => must have ship, 'S' => must have ship."""
        all_cells = set()
        for ship_positions in layout:
            all_cells.update(ship_positions)

        for r in range(self.board_size):
            for c in range(self.board_size):
                val = grid[r][c]
                if val == 'M' and (r,c) in all_cells:
                    return True
                if val == 'H' and (r,c) not in all_cells:
                    return True
                if val == 'S' and (r,c) not in all_cells:
                    return True
        return False

    def _resample(self, states, weights, new_count):
        """Multinomial resampling from states given their weights. Return new (states, weights)."""
        if not states:
            return [], []
        cdf = []
        running = 0.0
        for w in weights:
            running += w
            cdf.append(running)

        new_states = []
        for _ in range(new_count):
            x = random.random()
            i = 0
            while i < len(cdf) and x > cdf[i]:
                i += 1
            if i == len(cdf):
                i = len(cdf)-1
            new_states.append(states[i])

        # new weights are uniform
        wval = 1.0/new_count
        new_weights = [wval]*new_count
        return (new_states, new_weights)
