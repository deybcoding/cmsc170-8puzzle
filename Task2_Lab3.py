"""
CMSC 170 - Laboratory Exercise No. 3
Task 2: 8-Puzzle Game in Python 

State representation
--------------------
A state is a flat list of 9 items read left-to-right, top-to-bottom.
Tiles are the ints 1..8 and the blank is the string ' '.
    [1, 2, 3, 4, ' ', 8, 5, 6, 7]   ->   1 2 3
                                          4 _ 8
                                          5 6 7
Index -> (row, col):  row = i // 3, col = i % 3

Moves are described by the direction the EMPTY block moves:
    W = up, A = left, X = down, D = right
"""

import ast

BLANK = ' '
SIZE = 3
DEFAULT_GOAL = [1, 2, 3, 4, 5, 6, 7, 8, BLANK]  # Goal State A from the lab sheet

# key -> (label, row change, column change) for the empty block
MOVES = {
    'W': ('Up', -1, 0),
    'A': ('Left', 0, -1),
    'X': ('Down', 1, 0),
    'D': ('Right', 0, 1),
}


# ---------------------------------------------------------------- validation
def is_valid_state(state):
    """A state is valid iff it is a list of 9 items: tiles 1-8 once each + one blank."""
    if not isinstance(state, list) or len(state) != SIZE * SIZE:
        return False
    return sorted(state, key=str) == sorted(list(range(1, 9)) + [BLANK], key=str)


def _inversions(state):
    tiles = [t for t in state if t != BLANK]
    return sum(1 for i in range(len(tiles)) for j in range(i + 1, len(tiles))
               if tiles[i] > tiles[j])


def is_solvable(initial, goal):
    """On a 3x3 board, goal is reachable iff both states have the same inversion parity."""
    return _inversions(initial) % 2 == _inversions(goal) % 2


# --------------------------------------------------------------------- moves
def get_possible_moves(state):
    """Return {key: new_state} for every legal move of the empty block."""
    blank = state.index(BLANK)
    row, col = divmod(blank, SIZE)
    result = {}
    for key, (_, dr, dc) in MOVES.items():
        r, c = row + dr, col + dc
        if 0 <= r < SIZE and 0 <= c < SIZE:      # stay on the board
            new_state = state[:]
            target = r * SIZE + c
            new_state[blank], new_state[target] = new_state[target], new_state[blank]
            result[key] = new_state
    return result


def validate_move(state, key):
    """True iff `key` is a known move key AND that move is legal from `state`."""
    return key in MOVES and key in get_possible_moves(state)


# ------------------------------------------------------------------- display
def print_board(state):
    print("+---+---+---+")
    for r in range(SIZE):
        row = state[r * SIZE:(r + 1) * SIZE]
        print("| " + " | ".join(str(t) for t in row) + " |")
        print("+---+---+---+")


def show_instructions():
    print("8-Puzzle Game Start")
    print("The 8-puzzle problem is a 3x3 board with 8 tiles")
    print("numbered from 1 to 8 and one empty space.\n")
    print("The objective is to begin with an arbitrary")
    print("configuration of tiles, and move them to match")
    print("the final configuration.\n")
    print("Rules:")
    print("1. Input the initial state and goal state of the puzzle using")
    print("   this format:")
    print("     [1, 2, 3, 4, ' ', 8, 5, 6, 7]")
    print("2. Use the following keys to move the empty")
    print("   block:")
    print("     'W' Move Up       'A' Move Left")
    print("     'X' Move Down     'D' Move Right")
    print("   ('Q' quits the game)\n")


def read_state(prompt, default=None):
    """Keep asking until the user types a valid state (or Enter for the default)."""
    while True:
        text = input(prompt).strip()
        if not text and default is not None:
            return default[:]
        try:
            state = ast.literal_eval(text)
        except (ValueError, SyntaxError):
            print("  Could not read that. Use the format [1, 2, 3, 4, ' ', 8, 5, 6, 7]")
            continue
        if not is_valid_state(state):
            print("  Invalid state: use tiles 1-8 exactly once plus one ' ' (9 items).")
            continue
        return state


# ---------------------------------------------------------------------- game
def play():
    show_instructions()
    initial = read_state("Initial state: ")
    goal = read_state("Goal state (press Enter for 1-8 then blank): ", DEFAULT_GOAL)

    if not is_solvable(initial, goal):
        print("\nThis initial state can never reach that goal (parity mismatch).")
        print("Please restart with a different pair.")
        return

    state, moves = initial[:], 0
    while state != goal:
        print(f"\nMoves so far: {moves}")
        print_board(state)
        options = get_possible_moves(state)
        print("Available: " + ", ".join(f"'{k}' {MOVES[k][0]}" for k in options))
        key = input("Your move: ").strip().upper()
        if key == 'Q':
            print("Game ended.")
            return
        if not validate_move(state, key):
            print("  Invalid move! The empty block can't go there (or unknown key).")
            continue
        state = options[key]
        moves += 1

    print()
    print_board(state)
    print(f"Solved in {moves} moves!")


if __name__ == "__main__":
    play()
