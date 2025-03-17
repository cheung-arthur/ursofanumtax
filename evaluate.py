import sys
from battleship.board import Board
from battleship.random_bot import RandomBot
from battleship.monte_carlo_heuristics_bot import MonteCarloHeuristicsBot
from battleship.monte_carlo_hmm_bot import MonteCarloHMMBot
from battleship.empirical_hmm_bot import EmpiricalHMMBot

def simulate_game(bot_class):
    """Simulates a single game for a given bot class and returns the number of guesses."""
    board = Board()
    bot = bot_class(board_size=board.size)
    guess_count = 0

    while not board.all_ships_sunk():
        move = bot.choose_move()
        # In case no moves are left (should not happen in a standard game)
        if move is None:
            break
        result = board.attack(move)
        bot.update_knowledge(move, result)
        guess_count += 1

    return guess_count

def evaluate_bot(bot_class, num_games):
    """Runs num_games simulations for a given bot and returns the average number of guesses."""
    total_guesses = 0
    for _ in range(num_games):
        total_guesses += simulate_game(bot_class)
    return total_guesses / num_games

def main():
    # Set default number of games to 100; override if provided as a command-line argument.
    num_games = 100
    if len(sys.argv) > 1:
        try:
            num_games = int(sys.argv[1])
        except ValueError:
            print("Invalid number of games specified. Using default of 100 games.")

    # List of bots to evaluate: (name, bot class)
    bots = [
        ("RandomBot", RandomBot),
        ("MonteCarloHeuristicsBot", MonteCarloHeuristicsBot),
        ("MonteCarloHMMBot", MonteCarloHMMBot),
        ("EmpiricalHMMBot", EmpiricalHMMBot)
    ]

    # Run evaluation for each bot and print average guesses.
    for bot_name, bot_class in bots:
        avg_guesses = evaluate_bot(bot_class, num_games)
        print(f"{bot_name} average number of guesses over {num_games} games: {avg_guesses:.2f}")

if __name__ == '__main__':
    main()
