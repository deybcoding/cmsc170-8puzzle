"""
CMSC 170 - Laboratory Exercise No. 3
Task 2: 8-Puzzle Game in Python 

State representation
--------------------
A state is a tuple of 9 ints read left-to-right, top-to-bottom, and the blank is 0.
The Task 3 file uses the same form, so the game and the search hand states to each
other without converting anything.
    (1, 2, 3, 4, 0, 8, 5, 6, 7)   ->   1 2 3
                                      4 _ 8
                                      5 6 7
Index -> (row, col):  row = i // 3, col = i % 3

The player still types the format from the lab sheet, [1, 2, 3, 4, ' ', 8, 5, 6, 7].
to_state() converts that in one place: a blank typed as ' ', '_' or 0 becomes 0.

This file owns the shared move rules (MOVES, get_possible_moves, validate_move) and
the parity check, and the Task 3 search imports them.

Moves are described by the direction the EMPTY block moves:
    W = up, A = left, X = down, D = right
"""

import ast
import random

BLANK = 0
SIZE = 3
BLANK_CHARS = (' ', '_', '')        # what the player is allowed to type for the blank
DEFAULT_GOAL = (1, 2, 3, 4, 5, 6, 7, 8, BLANK)  # Goal State A from the lab sheet

# key -> (label, row change, column change) for the empty block
MOVES = {
    'W': ('Up', -1, 0),
    'A': ('Left', 0, -1),
    'X': ('Down', 1, 0),
    'D': ('Right', 0, 1),
}


# ---------------------------------------------------------------- validation
def is_valid_state(state):
    """True iff state is 9 ints: the tiles 1-8 once each plus one blank (0)."""
    return (isinstance(state, (tuple, list)) and len(state) == SIZE * SIZE
            and all(isinstance(t, int) and not isinstance(t, bool) for t in state)
            and sorted(state) == list(range(SIZE * SIZE)))


def to_state(items):
    """Convert what the player typed into a state, or raise ValueError.

    The blank may be typed as ' ' instead of 0, so this is where the typed form
    becomes the form everything else works with.
    """
    if not isinstance(items, list) or len(items) != SIZE * SIZE:
        raise ValueError("needs 9 items inside square brackets")
    converted = []
    for item in items:
        if isinstance(item, str) and item.strip() in BLANK_CHARS:
            converted.append(BLANK)
        elif isinstance(item, int) and not isinstance(item, bool):
            converted.append(item)
        else:
            raise ValueError(f"{item!r} is not a tile number or a blank")
    state = tuple(converted)
    if not is_valid_state(state):
        raise ValueError("use the tiles 1-8 exactly once plus one blank")
    return state


def _inversions(state):
    tiles = [t for t in state if t != BLANK]
    return sum(1 for i in range(len(tiles)) for j in range(i + 1, len(tiles))
               if tiles[i] > tiles[j])


def is_solvable(initial, goal):
    """On a 3x3 board, goal is reachable iff both states have the same inversion parity."""
    return _inversions(initial) % 2 == _inversions(goal) % 2


def random_state(goal=DEFAULT_GOAL, steps=60):
    """A random board that can reach the goal.

    It is made by playing random legal moves from the goal, so the board it returns is
    always solvable to that goal, and no move undoes the one before it so the board
    does not wander back to the goal.
    """
    undo = {'W': 'X', 'X': 'W', 'A': 'D', 'D': 'A'}
    state, previous = goal, None
    for _ in range(steps):
        options = get_possible_moves(state)
        choices = [key for key in options if key != previous] or list(options)
        key = random.choice(choices)
        state = options[key]
        previous = undo[key]
    return state if state != goal else random_state(goal, steps + 10)


# --------------------------------------------------------------------- moves
def get_possible_moves(state):
    """Return {key: new_state} for every legal move of the empty block.

    This is the project's only move generator. The Task 3 search calls this same
    function, so the game and the search cannot disagree about the rules.
    """
    blank = state.index(BLANK)
    row, col = divmod(blank, SIZE)
    result = {}
    for key, (_, dr, dc) in MOVES.items():
        r, c = row + dr, col + dc
        if 0 <= r < SIZE and 0 <= c < SIZE:      # stay on the board
            target = r * SIZE + c
            tiles = list(state)
            tiles[blank], tiles[target] = tiles[target], tiles[blank]
            result[key] = tuple(tiles)
    return result


def validate_move(state, key):
    """True iff `key` is a known move key AND that move is legal from `state`."""
    return key in MOVES and key in get_possible_moves(state)


# ------------------------------------------------------------------- display
def print_board(state):
    print("+---+---+---+")
    for r in range(SIZE):
        row = state[r * SIZE:(r + 1) * SIZE]
        print("| " + " | ".join(" " if t == BLANK else str(t) for t in row) + " |")
        print("+---+---+---+")


# The description of the game, in one place: the CLI prints it and the window shows it,
# so both ways of playing explain the puzzle the same way.
GAME_DESCRIPTION = """8-Puzzle Game Start
The 8-puzzle problem is a 3x3 board with 8 tiles
numbered from 1 to 8 and one empty space.

The objective is to begin with an arbitrary
configuration of tiles, and move them to match
the final configuration.

How the board is written
   The nine cells are read row by row, left to right, and the empty space is a blank.
   The board below is the one written as [1, 2, 3, 4, ' ', 8, 5, 6, 7] in the puzzle's
   input format:

        1   2   3
        4       8
        5   6   7

How a move works
   You never move a tile directly. You move the EMPTY SPACE, and the tile on that side
   of it slides into the space, so those two cells swap. That is why the keys below are
   named after the direction the space moves: 'W' moves the space up, which slides the
   tile above it down.

   Only a tile next to the space can move. Nothing jumps and nothing moves diagonally,
   so a space in a corner has two possible moves, one on an edge has three, and one in
   the middle has four. The game prints the moves available after every move.

How you win
   The puzzle is finished when every tile and the empty space match the goal board. The
   counter goes up by one for every move you make, and the game says how many moves it
   took when you get there.

Rules
   1. Input the initial state and goal state of the puzzle using this format:
        [1, 2, 3, 4, ' ', 8, 5, 6, 7]
      The empty space may also be typed as 0 or '_'.
   2. Use the following keys to move the empty block:
        'W' Move Up       'A' Move Left
        'X' Move Down     'D' Move Right
      ('R' at the first prompt gives a random board that can reach the default goal)
      ('Q' quits, and you can then watch BFS solve the board you are on)
   3. Not every board can reach every other board: half of the arrangements cannot be
      reached from a given start, so the game checks the two boards you give it and
      tells you straight away when the goal cannot be reached."""


def show_instructions():
    """Print the description of the puzzle and the rules, before anything is asked."""
    print(GAME_DESCRIPTION)
    print()


def read_state(prompt, default=None, random_from=None):
    """Keep asking until the user types a valid state (or Enter for the default).

    The typed list is converted with to_state() here, so everything after this
    point works with the blank as 0. 'R' asks for a random board when random_from
    is given, and 'Q' and Ctrl-D both stop the game cleanly.
    """
    while True:
        try:
            text = input(prompt).strip()
        except EOFError:
            print("\nNo input left, ending the game.")
            raise SystemExit(0)
        if text.upper() == 'Q':
            print("Game ended.")
            raise SystemExit(0)
        if text.upper() == 'R' and random_from is not None:
            board = random_state(random_from)
            print("  random board: " + str(board))
            return board
        if not text and default is not None:
            return default
        try:
            return to_state(ast.literal_eval(text))
        except (ValueError, SyntaxError) as error:
            print(f"  Could not read that ({error}). Use the format "
                  "[1, 2, 3, 4, ' ', 8, 5, 6, 7]")


# ---------------------------------------------------------------------- game
def play(initial=None, goal=None, instructions=True):
    """The game. Returns (how it ended, initial, goal, moves played, final board).

    `initial` and `goal` are used when the boards were already read from a file.
    `instructions` is False when the player asked not to print the description, which
    is long: the rules are still printed by show_instructions() when it is called.
    """
    if instructions:
        show_instructions()
    if initial is None:
        initial = read_state("Initial state ('R' for a random board): ",
                             random_from=DEFAULT_GOAL)
    else:
        print("Initial state:")
        print_board(initial)
    if goal is None:
        goal = read_state("Goal state (press Enter for 1-8 then blank): ", DEFAULT_GOAL)
    else:
        print("Goal state:")
        print_board(goal)

    if not is_solvable(initial, goal):
        print("\nThis initial state can never reach that goal (parity mismatch).")
        print("Please restart with a different pair.")
        return ("unsolvable", initial, goal, 0, initial)

    state, moves = initial, 0
    while state != goal:
        print(f"\nMoves so far: {moves}")
        print_board(state)
        options = get_possible_moves(state)
        print("Available: " + ", ".join(f"'{k}' {MOVES[k][0]}" for k in options))
        try:
            key = input("Your move: ").strip().upper()
        except EOFError:
            print("\nNo input left, ending the game.")
            return ("no_input", initial, goal, moves, state)
        if key == 'Q':
            print("Game ended.")
            return ("quit", initial, goal, moves, state)
        if not validate_move(state, key):
            print("  Invalid move! The empty block can't go there (or unknown key).")
            continue
        state = options[key]
        moves += 1

    print()
    print_board(state)
    print(f"Solved in {moves} moves!")
    return ("solved", initial, goal, moves, state)


if __name__ == "__main__":
    play()
