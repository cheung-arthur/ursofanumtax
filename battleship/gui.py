import pygame
import sys
import time

# A few color constants (R, G, B)
COLOR_BG        = (30, 30, 30)
COLOR_UNKNOWN   = (50, 50, 200)   # darkish blue
COLOR_MISS      = (200, 200, 200) # light gray
COLOR_HIT       = (255, 0, 0)     # bright red
COLOR_SUNK      = (128, 0, 0)     # darker red
COLOR_GRID_LINE = (0, 0, 0)
COLOR_TEXT      = (255, 255, 255)

CELL_SIZE = 30
CELL_MARGIN = 2
FONT_SIZE = 20
UPDATE_DELAY_MS = 0  # Wait 0.5s between moves

def cell_state(board, r, c):
    """
    Return one of: 'unknown', 'miss', 'hit', or 'sunk', 
    based on whether (r,c) has been guessed and if it belongs to a sunk ship.
    """
    if (r, c) not in board.guesses:
        return 'unknown'
    else:
        # If guessed, see if it hits any ship
        for ship in board.ships:
            if (r, c) in ship.positions:
                # It's a hit; check if that entire ship is sunk
                if ship.is_sunk():
                    return 'sunk'
                else:
                    return 'hit'
        # If we didn't find a ship containing (r,c), it's a miss
        return 'miss'

def draw_board(screen, board, offset_x, offset_y, label=""):
    """
    Draw a single board at (offset_x, offset_y).
    Label is drawn above the board.
    """
    font = pygame.font.SysFont(None, FONT_SIZE)
    # Draw label
    label_surf = font.render(label, True, COLOR_TEXT)
    screen.blit(label_surf, (offset_x, offset_y - FONT_SIZE - 5))

    for r in range(board.size):
        for c in range(board.size):
            state = cell_state(board, r, c)
            if state == 'unknown':
                color = COLOR_UNKNOWN
            elif state == 'miss':
                color = COLOR_MISS
            elif state == 'hit':
                color = COLOR_HIT
            elif state == 'sunk':
                color = COLOR_SUNK
            else:
                color = COLOR_UNKNOWN

            cell_x = offset_x + c * (CELL_SIZE + CELL_MARGIN)
            cell_y = offset_y + r * (CELL_SIZE + CELL_MARGIN)
            pygame.draw.rect(screen, color, (cell_x, cell_y, CELL_SIZE, CELL_SIZE))

def run_gui(bots, boards):
    """
    Runs a pygame window showing each board side by side. 
    Each bot/board pair is stepped in a round-robin manner.
    """
    pygame.init()
    font = pygame.font.SysFont(None, FONT_SIZE)

    # We'll lay out each board horizontally. 
    # So total width = (board_count * board_width) + some margin
    board_count = len(boards)
    board_width = boards[0].size * (CELL_SIZE + CELL_MARGIN)
    board_height = boards[0].size * (CELL_SIZE + CELL_MARGIN)
    window_width = board_count * (board_width + 50)
    window_height = board_height + 100

    screen = pygame.display.set_mode((window_width, window_height))
    pygame.display.set_caption("Battleship GUI")

    guess_counts = [0]*board_count
    finished = [False]*board_count

    # We'll do round-robin moves: i=0 -> i=1 -> ... -> i=(n-1) -> back to i=0 ...
    current_bot_index = 0

    clock = pygame.time.Clock()
    running = True

    while running:
        # Handle events (like closing the window)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Check if all boards are finished
        if all(finished):
            # Done, just keep showing the final result
            pass
        else:
            # If the current bot is not finished, let it make a move
            if not finished[current_bot_index]:
                move = bots[current_bot_index].choose_move()
                if move is None:
                    # No moves left (edge case)
                    finished[current_bot_index] = True
                else:
                    result = boards[current_bot_index].attack(move)
                    guess_counts[current_bot_index] += 1
                    bots[current_bot_index].update_knowledge(move, result)
                    if boards[current_bot_index].all_ships_sunk():
                        finished[current_bot_index] = True

                # Wait a bit so we can see the move
                pygame.time.wait(UPDATE_DELAY_MS)

            # Move to the next bot
            current_bot_index = (current_bot_index + 1) % board_count

        # Draw everything
        screen.fill(COLOR_BG)

        for i, board in enumerate(boards):
            label = f"Bot {i} - {type(bots[i]).__name__} (Guesses={guess_counts[i]})"
            offset_x = 50 + i * (board_width + 50)
            offset_y = 50
            draw_board(screen, board, offset_x, offset_y, label)

        pygame.display.flip()
        clock.tick(60)  # up to 60 frames/sec

    pygame.quit()
    # Print final results in the console
    for i, bot in enumerate(bots):
        print(f"{type(bot).__name__} finished in {guess_counts[i]} guesses.")
