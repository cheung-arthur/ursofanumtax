# Contains the Bayesian Agent and belief-state classes
import chess
import numpy as np
from src.game_env import evaluate_board

class BeliefState:
    def __init__(self, color: chess.Color):
        # Initialize a probability vector for the 64 squares.
        # At the start, the opponent's pieces are in known positions.
        self.probabilities = np.zeros(64)
        board = chess.Board()
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.color != color:
                self.probabilities[square] = 1.0
        self.normalize()
    
    def normalize(self):
        total = self.probabilities.sum()
        if total > 0:
            self.probabilities /= total
    
    def update(self, evidence: float, squares):
        """
        Update belief state by multiplying probabilities for specified squares by an evidence factor.
        """
        for sq in squares:
            self.probabilities[sq] *= evidence
        self.normalize()
    
    def set_zero(self, square):
        self.probabilities[square] = 0.0
        self.normalize()
    
    def get_probability(self, square):
        return self.probabilities[square]

class BayesianAgent:
    def __init__(self, color: chess.Color):
        self.color = color
        self.belief_state = BeliefState(color)
        self.own_board = None  # This will be updated via umpire feedback.
    
    def observe(self, board: chess.Board):
        """
        Update internal observation of own pieces.
        """
        self.own_board = board
    
    def choose_move(self):
        """
        Choose a move from legal moves based on the current belief state.
        For simplicity, this example selects a random legal move.
        """
        legal_moves = list(self.own_board.legal_moves)
        if legal_moves:
            return np.random.choice(legal_moves)
        else:
            return None
    
    def update_belief(self, move_feedback, move: chess.Move):
        """
        Update the belief state based on umpire feedback.
        """
        if not move_feedback["legal"]:
            # If the move is illegal, increase the probability that the destination square is occupied.
            destination = move.to_square
            self.belief_state.update(evidence=1.5, squares=[destination])
        else:
            if move_feedback.get("capture", False):
                destination = move.to_square
                # Once a capture occurs, we are sure that square is empty.
                self.belief_state.set_zero(destination)