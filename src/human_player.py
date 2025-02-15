import chess

def get_human_move(observed_board: chess.Board):
    """
    Get a move from a human player.
    The user must enter moves in UCI format (e.g., 'e2e4').
    """
    move_str = input("Enter your move in UCI format (e.g., e2e4): ")
    try:
        move = chess.Move.from_uci(move_str.strip())
        return move
    except Exception:
        print("Invalid move format. Please try again.")
        return None