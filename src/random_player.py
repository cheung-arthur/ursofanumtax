import random
from umpire import KriegspielUmpire

class RandomAgent:
    def __init__(self, umpire: KriegspielUmpire):
        self.umpire = umpire

    def choose_move(self):
        if self.umpire.game_over:
            return

        board = self.umpire.board  # The ground truth
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return

        move = random.choice(legal_moves)
        success, announcements, final_square = self.umpire.move(move)
        print(f"Black plays {move}, success={success}")
        for ann in announcements:
            print("   Announcement:", ann)
        # We could print or log the announcements if desired
        # For now, let's just ignore them in RandomBot