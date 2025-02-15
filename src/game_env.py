# Contains the board, umpire, evaluation, and opponent move selection
import chess
import numpy as np

def get_player_view(board: chess.Board, color: chess.Color) -> chess.Board:
    """
    Returns a board view that only shows pieces for the given color.
    Opponent pieces are removed.
    """
    masked_board = board.copy(stack=False)
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.color != color:
            masked_board.remove_piece_at(square)
    return masked_board

class KriegspielBoard:
    def __init__(self):
        self.board = chess.Board()
    
    def apply_move(self, move: chess.Move):
        """
        Apply a move if legal; return outcome info.
        """
        if move in self.board.legal_moves:
            capture = self.board.is_capture(move)
            self.board.push(move)
            is_check = self.board.is_check()
            is_checkmate = self.board.is_checkmate()
            return {"legal": True, "capture": capture, "check": is_check,
                    "checkmate": is_checkmate}
        else:
            return {"legal": False}
    
    def get_full_state(self) -> chess.Board:
        return self.board.copy(stack=False)

class Umpire:
    def __init__(self):
        self.krieg_board = KriegspielBoard()
    
    def request_move(self, move: chess.Move, player_color: chess.Color):
        """
        Checks move legality against the full state.
        Returns feedback to the player/agent.
        """
        outcome = self.krieg_board.apply_move(move)
        return outcome
    
    def get_player_observation(self, player_color: chess.Color) -> chess.Board:
        """
        Return the board view for the given player.
        """
        return get_player_view(self.krieg_board.get_full_state(), player_color)
    
    def game_over(self):
        """
        Return True if game is over.
        """
        return self.krieg_board.board.is_game_over()
    
    def get_result(self):
        return self.krieg_board.board.result()

def evaluate_board(board: chess.Board, color: chess.Color) -> float:
    """
    A simple board evaluation function (material count).
    We assign pawn=1, knight=3, bishop=3, rook=5, queen=9.
    (King is not counted.)
    Positive value favors 'color', negative value favors the opponent.
    """
    piece_values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9
    }
    value = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            piece_value = piece_values.get(piece.piece_type, 0)
            if piece.color == color:
                value += piece_value
            else:
                value -= piece_value
    return value

def select_opponent_move(legal_moves, board: chess.Board, color: chess.Color, lambda_param=0.004):
    """
    Select an opponent move using a quantal response based on a simple board evaluation.
    This implements:
      P(move) ∝ exp(lambda * U(move))
    where U(move) is the board utility after making the move.
    """
    if not legal_moves:
        return None
    utilities = []
    for move in legal_moves:
        board_copy = board.copy(stack=False)
        board_copy.push(move)
        # Evaluate from the opponent's perspective.
        utility = evaluate_board(board_copy, color)
        utilities.append(utility)
    # Compute quantal response probabilities.
    exp_utilities = np.exp(np.array(utilities) * lambda_param)
    probabilities = exp_utilities / exp_utilities.sum()
    chosen_move = np.random.choice(legal_moves, p=probabilities)
    return chosen_move