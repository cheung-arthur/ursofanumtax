# main.py

import sys
from battleship.board import Board
from battleship.random_bot import RandomBot
from battleship.monte_carlo_bot import MonteCarloBot

# Map string names to classes
BOT_MAP = {
    'random': RandomBot,
    'montecarlo': MonteCarloBot
}

def play_bots(bot_names):
    """
    1) Generate a single random board.
    2) Extract the layout of that board.
    3) For each bot, create a *new* board with that layout.
    4) Let each bot fire at its board until all ships are sunk.
    5) Print how many guesses each bot needed.
    """

    # Convert the names to actual classes
    bot_classes = []
    for name in bot_names:
        name = name.strip().lower()
        if name not in BOT_MAP:
            raise ValueError(f"Unknown bot type '{name}'. Valid: {list(BOT_MAP.keys())}")
        bot_classes.append(BOT_MAP[name])

    # 1) Generate a random board and get its layout
    reference_board = Board()  # random
    layout = reference_board.get_layout()

    # 2) Create a new board for each bot
    boards = [Board.from_layout(layout, 10) for _ in bot_classes]
    bots = [cls(board_size=10) for cls in bot_classes]

    guess_counts = [0] * len(bots)
    finished = [False] * len(bots)

    # 3) Let them "play" in parallel on separate boards
    while not all(finished):
        for i, bot in enumerate(bots):
            if finished[i]:
                continue
            move = bot.choose_move()
            if move is None:
                # No moves left (should never happen in normal Battleship)
                finished[i] = True
                continue
            result = boards[i].attack(move)
            guess_counts[i] += 1
            bot.update_knowledge(move, result)
            if boards[i].all_ships_sunk():
                finished[i] = True

    # 4) Print results
    for i, cls in enumerate(bot_classes):
        print(f"{cls.__name__} finished in {guess_counts[i]} guesses.")

def main():
    # e.g. `python main.py random,montecarlo`
    if len(sys.argv) < 2:
        bot_names = ['random']  # default if no arguments
    else:
        bot_names = sys.argv[1].split(',')

    play_bots(bot_names)

if __name__ == "__main__":
    main()
