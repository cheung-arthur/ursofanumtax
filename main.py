import sys
from battleship.board import Board
from battleship.game import Game       
from battleship.random_bot import RandomBot
from battleship.monte_carlo_heuristics_bot import MonteCarloHeuristicsBot
from battleship.monte_carlo_hmm_bot import MonteCarloHMMBot
from battleship.empirical_hmm_bot import EmpiricalHMMBot
from battleship.gui import run_gui      


BOT_MAP = {
    'random': RandomBot,
    'montecarlo': MonteCarloHeuristicsBot,
    'montecarlohmm':  MonteCarloHMMBot,
    'hmm': EmpiricalHMMBot
}

def play_bots(bot_names):
    """
    Runs multiple bots in text-based mode (no GUI).
    Each bot gets its own Board with the same layout.
    Shows each guess and its result in the terminal.
    """
    # Convert the names to actual classes
    bot_classes = []
    for name in bot_names:
        name = name.strip().lower()
        if name not in BOT_MAP:
            raise ValueError(f"Unknown bot type '{name}'. Valid bots: {list(BOT_MAP.keys())}")
        bot_classes.append(BOT_MAP[name])

    # Generate a random board and copy its layout
    reference_board = Board()
    layout = reference_board.get_layout()

    boards = [Board.from_layout(layout, 10) for _ in bot_classes]
    bots = [cls(board_size=10) for cls in bot_classes]

    guess_counts = [0] * len(bots)
    finished = [False] * len(bots)

    # Round-robin until all boards are sunk
    while not all(finished):
        for i, bot in enumerate(bots):
            if finished[i]:
                continue

            # Bot chooses a move (some bots may return a list; pick the first)
            moves = bot.choose_move()
            if isinstance(moves, list) and len(moves) > 0:
                move = moves[0]
            else:
                move = moves

            if move is None:
                # No moves left
                finished[i] = True
                continue

            # Perform the attack
            result = boards[i].attack(move)
            guess_counts[i] += 1

            # Announce the guess and outcome
            row, col = move
            coord_str = f"{chr(ord('A') + col)}{row+1}"
            bot_name = type(bot).__name__
            print(f"{bot_name} guesses {coord_str} -> {result}")

            # Update the bot’s knowledge
            bot.update_knowledge(move, result)

            # Check if this board is now fully sunk
            if boards[i].all_ships_sunk():
                finished[i] = True

    # Print final results
    for i, cls in enumerate(bot_classes):
        print(f"{cls.__name__} finished in {guess_counts[i]} guesses.")


def play_bots_gui(bot_names):
    """
    Runs multiple bots in GUI mode.
    """
    bot_classes = []
    for name in bot_names:
        name = name.strip().lower()
        if name not in BOT_MAP:
            raise ValueError(f"Unknown bot type '{name}'. Valid bots: {list(BOT_MAP.keys())}")
        bot_classes.append(BOT_MAP[name])

    reference_board = Board()
    layout = reference_board.get_layout()

    boards = [Board.from_layout(layout, 10) for _ in bot_classes]
    bots = [cls(board_size=10) for cls in bot_classes]

    # Launch the pygame GUI loop
    run_gui(bots, boards)


def main():
    """
    Usage Examples:
      1) No args -> Start a normal text-based game with human input.
      2) python main.py random,montecarlo -> Run two bots in text mode, printing each guess & result.
      3) python main.py gui random,montecarlo -> Run two bots in the pygame GUI.
    """
    if len(sys.argv) < 2:
        # No arguments => run the human-playable, text-based game
        game = Game()
        game.play()
        return

    # We have at least one argument
    mode = sys.argv[1].lower()

    if mode == 'gui':
        # e.g. "python main.py gui random,montecarlo"
        if len(sys.argv) < 3:
            # default to one random bot if no second arg
            bot_names = ['random']
        else:
            bot_names = sys.argv[2].split(',')
        play_bots_gui(bot_names)

    else:
        # e.g. "python main.py random,montecarlo"
        # or "python main.py random"
        bot_names = mode.split(',')
        play_bots(bot_names)

if __name__ == "__main__":
    main()
