import argparse
from main import play_kriegspiel

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(
        description="Evaluate play_kriegspiel over multiple runs."
    )
    parser.add_argument(
        "times",
        type=int,
        nargs="?",
        default=100,
        help="Number of times to run play_kriegspiel (defaults to 100)."
    )
    args = parser.parse_args()

    wins = 0
    draws = 0
    losses = 0

    for _ in range(args.times):
        result = play_kriegspiel("/opt/homebrew/bin/stockfish")
        if result == "win":
            wins += 1
        elif result == "draw":
            draws += 1
        elif result == "loss":
            losses += 1
        else:
            pass

    print(f"Wins: {wins}")
    print(f"Draws: {draws}")
    print(f"Losses: {losses}")

if __name__ == "__main__":
    main()
