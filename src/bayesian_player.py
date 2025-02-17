import chess
import chess.engine
import random
import pickle
from umpire import KriegspielUmpire

class BayesianAgent:
    def __init__(self, 
                 umpire: KriegspielUmpire, 
                 stockfish_path: str, 
                 max_states: int = 2000,
                 use_dataset_init: bool = False,
                 dataset_file: str = "init_belief_states.pickle"):
        """
        If use_dataset_init=True, we load our initial belief states
        from the specified pickle file (dataset_file).
        Otherwise, we start from a single standard chess position.

        :param umpire: The KriegspielUmpire object with the ground-truth board
        :param stockfish_path: Path to the Stockfish (or other UCI) engine
        :param max_states: Maximum number of states we keep in our belief set
        :param use_dataset_init: Whether to load the initial belief from a pickle
        :param dataset_file: Path to the pickle file containing the initial belief
        """
        self.umpire = umpire
        self.max_states = max_states
        self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)

        if use_dataset_init:
            # Load belief states from the pickle file
            try:
                with open(dataset_file, "rb") as f:
                    self.belief_states = pickle.load(f)
                print(f"Loaded {len(self.belief_states)} belief states from {dataset_file}.")
            except Exception as e:
                print(f"Error loading belief states from {dataset_file}: {e}")
                print("Falling back to standard single-board initialization.")
                self.belief_states = [{
                    "board": chess.Board(),  # standard chess start
                    "weight": 1.0
                }]
        else:
            # Default to a single known state (standard chess starting position)
            self.belief_states = [{
                "board": chess.Board(),
                "weight": 1.0
            }]

    def normalize_beliefs(self):
        total = sum(s["weight"] for s in self.belief_states)
        if total > 0:
            for s in self.belief_states:
                s["weight"] /= total
        else:
            # If total = 0, all states are invalid
            self.belief_states = []

    def prune_states(self):
        # If we have more than self.max_states, prune the lowest-weight ones
        if len(self.belief_states) <= self.max_states:
            return
        # Sort states by descending weight
        self.belief_states.sort(key=lambda s: s["weight"], reverse=True)
        self.belief_states = self.belief_states[:self.max_states]
        self.normalize_beliefs()

    def update_belief_on_opponent_move(self, opp_final_square: chess.Square, announcements: list):
        """
        The opponent has just moved. We know the final square of that move
        (opp_final_square) and the announcements.
        We regenerate belief states accordingly.
        """
        new_belief_states = []

        for state in self.belief_states:
            board = state["board"]
            w = state["weight"]

            # Gather all legal moves in this hypothetical board
            legal_moves = list(board.legal_moves)

            candidate_moves = []
            for mv in legal_moves:
                # We want moves by the opponent (board.turn).
                # If that piece ends up on opp_final_square, we consider it.
                if mv.to_square == opp_final_square and board.color_at(mv.from_square) == board.turn:
                    candidate_moves.append(mv)

            if not candidate_moves:
                # This state can't explain the opponent's final square => prune it
                continue

            # For each candidate move, create a new board state
            for mv in candidate_moves:
                new_board = board.copy()
                new_board.push(mv)
                new_belief_states.append({
                    "board": new_board,
                    "weight": w
                })

        # Now apply the announcements to prune or adjust weights
        filtered_states = []
        for s in new_belief_states:
            board_after = s["board"]
            keep_it = True

            for ann in announcements:
                if ann.startswith("Pawn gone on "):
                    sq_str = ann.split()[-1]  # e.g. "d4"
                    sq = chess.parse_square(sq_str)
                    piece_captured = board_after.piece_at(sq)
                    # If there's a piece, it must be a pawn of the captured side
                    if piece_captured is not None and piece_captured.piece_type != chess.PAWN:
                        keep_it = False
                        break
                    if piece_captured is None:
                        keep_it = False
                        break
                elif ann.startswith("Piece gone on "):
                    sq_str = ann.split()[-1]
                    sq = chess.parse_square(sq_str)
                    piece_captured = board_after.piece_at(sq)
                    # If there's a piece, it must NOT be a pawn
                    if piece_captured is not None and piece_captured.piece_type == chess.PAWN:
                        keep_it = False
                        break
                    if piece_captured is None:
                        keep_it = False
                        break
                elif ann in ["Hell no", "No"]:
                    # Move was declared illegal in reality, 
                    # but we applied it => contradiction
                    keep_it = False
                    break
                elif ann.startswith("Check"):
                    # The board_after must be in check from the side that moved
                    if not board_after.is_check():
                        keep_it = False
                        break
                elif ann == "Checkmate":
                    if not board_after.is_checkmate():
                        keep_it = False
                        break
                elif ann == "Stalemate":
                    if not board_after.is_stalemate():
                        keep_it = False
                        break
                elif ann.startswith("draw"):
                    # If there's a draw claim, we do minimal checking
                    if not board_after.is_game_over():
                        keep_it = False
                        break
                # "White to move"/"Black to move" not strictly needed for pruning

            if keep_it:
                filtered_states.append(s)

        self.belief_states = filtered_states
        self.normalize_beliefs()
        self.prune_states()

    def update_belief_on_own_move_feedback(self, move: chess.Move, success: bool, announcements: list):
        """
        After we attempt a move, the umpire might say 'No'/'Hell no' (illegal)
        or we get captures/check etc. We'll prune states accordingly.
        """
        if not success:
            # Real board says illegal => 
            # prune states where the move would have been legal
            new_belief = []
            for s in self.belief_states:
                board = s["board"]
                if move in board.legal_moves:
                    continue  # this state conflicts with reality
                new_belief.append(s)
            self.belief_states = new_belief
            self.normalize_beliefs()
            self.prune_states()
            return

        # If success = True, apply the move to each consistent state
        new_belief_states = []
        for state in self.belief_states:
            board = state["board"]
            if move in board.legal_moves:
                new_board = board.copy()
                new_board.push(move)
                new_belief_states.append({
                    "board": new_board,
                    "weight": state["weight"]
                })

        # Now apply the announcements for further pruning
        filtered_states = []
        for s in new_belief_states:
            board_after = s["board"]
            keep_it = True

            for ann in announcements:
                if ann.startswith("Pawn gone on "):
                    sq_str = ann.split()[-1]
                    sq = chess.parse_square(sq_str)
                    piece_captured = board_after.piece_at(sq)
                    if piece_captured is not None and piece_captured.piece_type != chess.PAWN:
                        keep_it = False
                        break
                    if piece_captured is None:
                        keep_it = False
                        break
                elif ann.startswith("Piece gone on "):
                    sq_str = ann.split()[-1]
                    sq = chess.parse_square(sq_str)
                    piece_captured = board_after.piece_at(sq)
                    if piece_captured is not None and piece_captured.piece_type == chess.PAWN:
                        keep_it = False
                        break
                    if piece_captured is None:
                        keep_it = False
                        break
                elif ann.startswith("Check"):
                    if not board_after.is_check():
                        keep_it = False
                        break
                elif ann == "Checkmate":
                    if not board_after.is_checkmate():
                        keep_it = False
                        break
                elif ann == "Stalemate":
                    if not board_after.is_stalemate():
                        keep_it = False
                        break
                elif ann.startswith("draw"):
                    if not board_after.is_game_over():
                        keep_it = False
                        break

            if keep_it:
                filtered_states.append(s)

        self.belief_states = filtered_states
        self.normalize_beliefs()
        self.prune_states()

    def choose_move(self):
        """
        Choose our next move:
         - If we have no belief states, do random fallback using the real board.
         - Otherwise, pick the highest-weight state, feed it into Stockfish,
           and return the recommended move.
        """
        if not self.belief_states:
            # Fallback: random from the ground-truth board
            board_real = self.umpire.board
            legal_moves = list(board_real.legal_moves)
            if legal_moves:
                return random.choice(legal_moves)
            else:
                return None

        # Otherwise, pick the highest-prob state
        self.belief_states.sort(key=lambda s: s["weight"], reverse=True)
        best_state = self.belief_states[0]
        board_for_engine = best_state["board"].copy()

        # Use Stockfish
        result = self.engine.play(board_for_engine, limit=chess.engine.Limit(depth=12))
        return result.move
    

    def shutdown_engine(self):
        self.engine.quit()
