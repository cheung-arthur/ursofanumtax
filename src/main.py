# Main game loop (choose human mode or agent mode)
import argparse
import chess
import numpy as np

from src.game_env import Umpire, select_opponent_move
from src.bayesian_agent import BayesianAgent
from src.human_player import get_human_move

def play_game_human():
    """
    Play a game with a human player (as White) versus an opponent using quantal response.
    This version hides the exact opponent move to preserve Kriegspiel secrecy.
    """
    umpire = Umpire()
    human_color = chess.WHITE
    
    print("Welcome to Kriegspiel (Human Mode)!")
    print("You are playing as White.\n")
    
    while not umpire.game_over():
        # Human Turn
        print("\n--- Human Turn ---")
        observation = umpire.get_player_observation(human_color)
        
        # Show the masked board (only your pieces visible)
        print("Your view of the board:")
        print(observation)
        
        move = None
        while move is None:
            move = get_human_move(observation)
            if move not in observation.legal_moves:
                print("That move appears illegal based on your visible pieces. Try again.")
                move = None
        
        feedback = umpire.request_move(move, human_color)
        if not feedback["legal"]:
            print("Umpire: Illegal move. Try again.")
            continue
        else:
            if feedback.get("capture", False):
                print("Umpire: A capture has occurred.")
            if feedback.get("check", False):
                print("Umpire: Check!")
            if feedback.get("checkmate", False):
                print("Umpire: Checkmate!")
        
        # Opponent Turn
        if not umpire.game_over():
            print("\n--- Opponent Turn ---")
            opp_color = not human_color
            legal_moves = list(umpire.krieg_board.board.legal_moves)
            opp_move = select_opponent_move(legal_moves, umpire.krieg_board.board, opp_color)
            
            # Hide the actual move from you (the human) to simulate Kriegspiel
            print("The opponent has moved (exact move hidden).")
            
            # Actually apply the move on the full board (umpire sees it)
            umpire.krieg_board.apply_move(opp_move)
    
    print("Game over. Result:", umpire.get_result())

def play_game_agent():
    """
    Play a game with the Bayesian Agent (as White) versus an opponent using quantal response.
    """
    umpire = Umpire()
    agent = BayesianAgent(chess.WHITE)
    
    print("Welcome to Kriegspiel (Agent Mode)!")
    print("Agent is playing as White.\n")
    
    while not umpire.game_over():
        # Agent Turn
        print("\n--- Agent Turn ---")
        observation = umpire.get_player_observation(agent.color)
        agent.observe(observation)
        move = agent.choose_move()
        
        if move is None:
            print("Agent has no legal moves available.")
            break
        
        print("Agent attempts move:", move)
        feedback = umpire.request_move(move, agent.color)
        agent.update_belief(feedback, move)
        
        if not feedback["legal"]:
            print("Umpire: Illegal move by agent.")
            continue
        
        if feedback.get("capture", False):
            print("Umpire: Capture occurred.")
        if feedback.get("check", False):
            print("Umpire: Check!")
        if feedback.get("checkmate", False):
            print("Umpire: Checkmate!")
        
        # Opponent Turn
        if not umpire.game_over():
            print("\n--- Opponent Turn ---")
            opp_color = not agent.color
            legal_moves = list(umpire.krieg_board.board.legal_moves)
            opp_move = select_opponent_move(legal_moves, umpire.krieg_board.board, opp_color)
            print("Opponent (bot) move (visible to us for debugging):", opp_move)
            umpire.krieg_board.apply_move(opp_move)
    
    print("Game over. Result:", umpire.get_result())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kriegspiel Chess Simulation")
    parser.add_argument('--mode', choices=['human', 'agent'], default='human',
                        help="Choose mode: 'human' to play manually, 'agent' to run the Bayesian Agent.")
    args = parser.parse_args()
    
    if args.mode == 'human':
        play_game_human()
    elif args.mode == 'agent':
        play_game_agent()
