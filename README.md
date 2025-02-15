# Kriegspiel Chess Bayesian Agent

This repository contains a Python implementation of a Kriegspiel Chess simulation environment, including:

- A game environment (`Umpire`, `KriegspielBoard`, and player view masking)
- A Bayesian Agent that maintains a belief state over the opponent's pieces and updates it via Bayesian inference.
- A human player mode to play the game manually.
- An opponent move selection function that uses a quantal response (inspired by the paper "Towards Strategic Kriegspiel Play with Opponent Modeling").

## Installation

1. Clone this repository.
2. Install the required packages:
```pip install -r requirements.txt```


## Usage

### To play as a human player:
Run:
```python src/main.py --mode human```

### To run the Bayesian Agent simulation:
Run:
```python src/main.py --mode agent```
