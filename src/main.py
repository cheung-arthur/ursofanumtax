import sys
import chess
from umpire import KriegspielUmpire
from random_player import RandomAgent
from bayesian_player import BayesianAgent

def play_kriegspiel(stockfish_path: str, use_dataset_init: bool = False, max_states: int = 2000):
    # 1. Create umpire
    umpire = KriegspielUmpire()

    # 2) Create White (PartialInfoAgent) and Black (RandomBot)
    white_agent = BayesianAgent(
        umpire,
        stockfish_path=stockfish_path,
        max_states=max_states,
        use_dataset_init=use_dataset_init
    )
    black_bot = RandomAgent(umpire)

    move_counter = 1

    while not umpire.game_over:
        current_color = umpire.get_active_color()

        if current_color == "White":
            # White: partial-info agent
            move = white_agent.choose_move()
            if move is None:
                # no legal moves or fallback
                print("White has no moves or agent gave None.")
                break

            success, announcements, final_sq = umpire.move(move)
            # White processes own move feedback
            white_agent.update_belief_on_own_move_feedback(move, success, announcements)

            # Print or log
            print(f"{move_counter}. White plays {move}, success={success}")
            for ann in announcements:
                print("   Announcement:", ann)

        else:
            # Black: random bot
            black_bot.make_move()
            success = not umpire.board.is_game_over()
            # The partial-info agent sees the final square of black's move if success
            # But we need to capture the last move from the ground-truth board:
            last_move = umpire.board.peek() if umpire.board.move_stack else None

            if last_move and not umpire.game_over:
                # Gather announcements from the *last* move
                # In our design, we get them from black_bot's 'make_move' 
                # but we didn't store them there. Let's store them now:
                # Actually, to keep it consistent, let's do a slight refactor:
                # For demonstration, let's assume we re-run the move or 
                # intercept the announcements in black_bot. 
                # We'll do a quick hack: no direct announcements for the partial-info agent 
                # unless we refactor RandomBot. 
                pass

                # We'll just get final square from last move
                opp_final_square = last_move.to_square
                # The White agent doesn't know exactly which piece moved, 
                # but it does know the final square (opp_final_square).
                # We'll assume we can't easily get the announcements unless 
                # we do more hooking. For demonstration, let's feed empty announcements.
                announcements = []  # In real code, we'd properly hook in the results.

                # White updates its beliefs
                white_agent.update_belief_on_opponent_move(opp_final_square, announcements)

            print(f"{move_counter}. Black (Random) played.")
        
        move_counter += 1
        if umpire.game_over:
            break

    print("Game over. Result:", umpire.result if umpire.result else "Unknown")
    # Shutdown Stockfish
    white_agent.shutdown_engine()

if __name__ == "__main__":
    # Run with arguments, or just set them here:
    # e.g. python main.py "/usr/local/bin/stockfish" True
    stockfish_path = sys.argv[1] if len(sys.argv) > 1 else "/opt/homebrew/bin/stockfish"
    use_dataset_init = bool(sys.argv[2]) if len(sys.argv) > 2 else False
    play_kriegspiel(stockfish_path, use_dataset_init, max_states=2000)
