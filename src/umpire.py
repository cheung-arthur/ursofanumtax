import chess
import chess.engine

class KriegspielUmpire:
    def __init__(self):
        # Start from a normal chess initial position
        self.board = chess.Board()
        self.game_over = False
        self.result = None

    def get_active_color(self):
        return "White" if self.board.turn == chess.WHITE else "Black"

    def is_move_physically_impossible(self, move: chess.Move) -> bool:
        """
        Check if the move is 'Hell no' / 'Impossible' — e.g., 
        a bishop that moves like a knight, or other piece type 
        mismatch which cannot be explained by the hidden state.
        We'll do a simplistic check:
        - If the piece on the source square does not exist or 
          is a different color or piece type that cannot possibly move 
          from src to dst in standard chess geometry.
        """
        piece = self.board.piece_at(move.from_square)
        if piece is None:
            return True  # No piece to move -> physically impossible
        # We can also check 'type of move' if it doesn't match piece's capabilities:
        # But python-chess's is_legal() might suffice to detect all impossible moves 
        # vs. truly illegal moves. We'll handle them differently:
        #   "Impossible" means the piece type doesn't match the move geometry at all.
        
        # We'll do a quick geometry check:
        #   If the board says it's not a pseudo-legal move for that piece, call it impossible.
        if move not in self.board.generate_pseudo_legal_moves():
            return True
        return False

    def move(self, move: chess.Move):
        """
        Attempt to apply the move to the ground-truth board.
        Returns a tuple:
          (success: bool, announcements: list[str], final_square: chess.Square or None)
        If success=False, we either have "No" or "Hell no".
        If success=True, announcements may include captures, checks, etc.
        final_square is the destination square if success=True, else None.
        """
        announcements = []

        # 1. If the move is physically impossible in standard chess geometry
        if self.is_move_physically_impossible(move):
            announcements.append("Hell no")
            return False, announcements, None

        # 2. Check if move is fully legal in the ground truth
        if move not in self.board.legal_moves:
            announcements.append("No")
            return False, announcements, None

        # Before making the move, let's see if there's a capture
        piece_captured = None
        if self.board.is_capture(move):
            # The piece on the destination might be captured
            piece_captured = self.board.piece_at(move.to_square)

        # 3. Make the move
        self.board.push(move)

        # 4. Announcements about captures
        if piece_captured:
            if piece_captured.piece_type == chess.PAWN:
                announcements.append(f"Pawn gone on {chess.square_name(move.to_square)}")
            else:
                announcements.append(f"Piece gone on {chess.square_name(move.to_square)}")

        # 5. Check for check, checkmate, or stalemate
        if self.board.is_check():
            # Determine the direction of check if possible
            # For simplicity, we do a minimal approach:
            check_announcement = self.identify_check_direction()
            announcements.append(check_announcement)

        if self.board.is_game_over():
            # Could be checkmate, stalemate, etc.
            result = self.board.result()  # e.g. "1-0", "0-1", "1/2-1/2"
            self.game_over = True
            self.result = result
            if self.board.is_checkmate():
                announcements.append("Checkmate")
            elif self.board.is_stalemate():
                announcements.append("Stalemate")
            elif self.board.is_insufficient_material():
                announcements.append("draw by insufficient force")
            elif self.board.can_claim_draw():
                # Could be 50-move or repetition, etc.
                # For demonstration, let's just say "draw"
                announcements.append("draw")

        # 6. "White to move" or "Black to move"
        if not self.game_over:
            color_move = "White to move" if self.board.turn == chess.WHITE else "Black to move"
            announcements.append(color_move)

        return True, announcements, move.to_square

    def identify_check_direction(self) -> str:
        """
        Returns a string describing the type/direction of check:
          - "Check on the vertical"
          - "Check on the horizontal"
          - "Check on the long diagonal"
          - "Check on the short diagonal"
          - "Check by a knight"
          etc.
        This is fairly naive logic. 
        """
        # The king in check is the board.turn's *opponent*'s king
        # Actually in python-chess, 'turn' is the side *to move* after pushing,
        # so the checking side is the side that just moved.
        king_square = self.board.king(not self.board.turn)
        if king_square is None:
            return "Check"  # fallback if no king found

        # Gather attackers
        attackers = self.board.attackers(self.board.turn, king_square)
        # If multiple attackers, just pick one for announcement:
        for sq in attackers:
            piece = self.board.piece_at(sq)
            if piece is not None:
                if piece.piece_type == chess.KNIGHT:
                    return "Check by a knight"
                if piece.piece_type == chess.ROOK:
                    # vertical/horizontal
                    file_src = chess.square_file(sq)
                    rank_src = chess.square_rank(sq)
                    file_king = chess.square_file(king_square)
                    rank_king = chess.square_rank(king_square)
                    if file_src == file_king:
                        return "Check on the vertical"
                    else:
                        return "Check on the horizontal"
                if piece.piece_type == chess.BISHOP or piece.piece_type == chess.QUEEN:
                    # diagonal
                    file_diff = abs(chess.square_file(sq) - chess.square_file(king_square))
                    rank_diff = abs(chess.square_rank(sq) - chess.square_rank(king_square))
                    if file_diff == rank_diff:
                        # Try to guess long vs short diagonal:
                        # If it's a big distance, call it 'long diagonal'; else 'short diagonal'.
                        if file_diff >= 3:
                            return "Check on the long diagonal"
                        else:
                            return "Check on the short diagonal"
                if piece.piece_type == chess.QUEEN:
                    # If the queen is attacking along file/rank
                    # we already might have returned above if we recognized rook-like or bishop-like
                    # but let's do a fallback:
                    return "Check"
        return "Check"  # fallback if uncertain
