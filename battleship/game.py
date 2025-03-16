from battleship.board import Board

class Game:
    def __init__(self):
        self.board = Board()
        self.turns = 0

    def play(self):
        print("Welcome to Battleship!")
        while not self.board.all_ships_sunk():
            user_input = input("Enter coordinate (A-J, 1-10): ")
            coord = self.parse_input(user_input)
            if coord is None:
                print("Invalid input. Please enter a letter A-J followed by a number 1-10 (e.g., A5).")
                continue

            result = self.board.attack(coord)
            if result == "already guessed":
                print("You already guessed that coordinate. Try a different one.")
                continue

            self.turns += 1
            print(result)

        print(f"Congratulations! You sunk all the ships in {self.turns} turns.")

    def parse_input(self, user_input):
        """
        Parses the user input and converts it into a board coordinate (row, col).
        Expected format: LetterNumber (e.g., A5)
        Returns a tuple (row, col) or None if the input is invalid.
        """
        user_input = user_input.strip().upper()
        if len(user_input) < 2:
            return None

        letter = user_input[0]
        if letter < 'A' or letter > 'J':
            return None

        try:
            number = int(user_input[1:])
        except ValueError:
            return None

        if number < 1 or number > 10:
            return None

        row = number - 1
        col = ord(letter) - ord('A')
        return (row, col)
