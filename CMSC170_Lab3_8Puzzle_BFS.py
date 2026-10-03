"""
DS 170 / CMSC 170 - Laboratory Exercise No. 3
8-Puzzle Problem and Breadth-First Search in Python

Group I
    Senoy, Kyle Howard          <student number>
    Royo, Dave Christian        <student number>
    Jomuad, Precious Mae E.     2023-00554

This is the group's single program for the lab. It has four parts:

    Part 1  the 8-puzzle game (Task 2): instructions, the initial state input, the
            move generator and the move validator
    Part 2  breadth-first search (Task 3): the Node class, the state space, the file
            input and the level-by-level output
    Part 3  the GUI (integration): play the puzzle in a window, and once it is solved
            watch BFS replay the optimal solution from the same board
    Part 4  the menu that starts any of the three

Run it from the folder that holds the input files:

    python3 CMSC170_Lab3_8Puzzle_BFS.py

The menu takes a choice; the GUI needs a desktop session. The three parts are also
importable, so the check batteries can drive them directly.

The parts were written by different members and joined here. Part 2 used to keep its
own copy of the move rules; it now calls Part 1's, so the game and the search can
never disagree about what a legal move is. The board is a tuple of nine ints with 0
for the blank everywhere inside the program; the player still types the lab sheet's
format, [1, 2, 3, 4, ' ', 8, 5, 6, 7], and to_state() converts it on the way in.
"""

import ast
import sys
import tkinter as tk
import tkinter.font as tkfont

from collections import deque

# ==============================================================================
# PART 1 - Task 2: the 8-puzzle game
# ==============================================================================

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
    """Keep asking until the user types a valid state (or Enter for the default).

    The typed list is converted with to_state() here, so everything after this
    point works with the blank as 0. 'Q' and Ctrl-D both stop the game cleanly.
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
        if not text and default is not None:
            return default
        try:
            return to_state(ast.literal_eval(text))
        except (ValueError, SyntaxError) as error:
            print(f"  Could not read that ({error}). Use the format "
                  "[1, 2, 3, 4, ' ', 8, 5, 6, 7]")


# ---------------------------------------------------------------------- game
def play():
    show_instructions()
    initial = read_state("Initial state: ")
    goal = read_state("Goal state (press Enter for 1-8 then blank): ", DEFAULT_GOAL)

    if not is_solvable(initial, goal):
        print("\nThis initial state can never reach that goal (parity mismatch).")
        print("Please restart with a different pair.")
        return

    state, moves = initial, 0
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

# ==============================================================================
# PART 2 - Task 3: breadth-first search
# ==============================================================================

# Describing BFS

def describe_bfs():
    print("""
=== Breadth-First Search (BFS) ===
BFS is an uninformed search. It starts at the root (initial state) and
explores ALL nodes at depth d before any node at depth d+1.

Because every move costs 1 and the queue is FIFO, the first time the
goal is reached is via a shortest path, so BFS is complete and optimal.
Time: O(V + E).  Space: O(V) (visited set + queue).
""")

# Node class

class Node:
    """One node in the search tree."""

    def __init__(self, state, parent=None, action=None, depth=0, path_cost=0):
        self.state = state          # tuple of 9 ints, 0 = blank
        self.parent = parent        # Node we came from (None for root)
        self.action = action        # move that produced this node
        self.depth = depth          # level in the search tree
        self.path_cost = path_cost  # g(n); each move costs 1 (useful for A* later)

    def path(self):
        """Walk parent pointers from this node back to the root."""
        node, nodes = self, []
        while node is not None:
            nodes.append(node)
            node = node.parent
        return nodes[::-1]          # root -> ... -> this node

    def __repr__(self):
        return f"Node(state={self.state}, depth={self.depth}, action={self.action})"


# Moves and state space

# The move generator is Part 1's get_possible_moves(state), defined above. It
# returns {action: next_state} for the blank's legal moves, so this section only
# has to cache the states the search expands.
STEP_COST = 1

# state_space: {state: [(action, next_state, step_cost), ...]}
# Filled while BFS runs, so it only stores states that were actually
# expanded. Storing the step cost lets the same code be extended to A*.
state_space = {}

def expand(state):
    """Return (and cache in state_space) the successors of a state."""
    if state not in state_space:
        state_space[state] = [(a, s, STEP_COST)
                              for a, s in get_possible_moves(state).items()]
    return state_space[state]


# File input

def validate_state(state, label="state"):
    if not is_valid_state(state):
        raise ValueError(f"Invalid {label}: must contain each of 0-8 exactly once, got {list(state)}")

def parse_state_file(path):
    """
    Read a file with two 3x3 blocks of comma-separated numbers
    (initial state, then goal state), 0 = blank. Blank lines between
    the blocks are allowed. Returns (initial_state, goal_state) as tuples.
    """
    with open(path) as f:
        rows = [line.strip() for line in f if line.strip()]
    if len(rows) != 6:
        raise ValueError(f"Expected 6 non-empty lines (two 3x3 blocks), found {len(rows)}.")
    grids = []
    for block in (rows[:3], rows[3:]):
        flat = []
        for line in block:
            parts = [p.strip() for p in line.split(",")]
            if len(parts) != 3:
                raise ValueError(f"Each row needs 3 comma-separated values: '{line}'")
            flat.extend(int(p) for p in parts)   # 0 stays 0 = blank, handled here at read time
        grids.append(tuple(flat))
    validate_state(grids[0], "initial state")
    validate_state(grids[1], "goal state")
    return grids[0], grids[1]


# Solvability check and BFS

# is_solvable(initial, goal) is Part 1's parity check. It lets the
# program reject an impossible board instead of exploring all 181,440 reachable
# states before giving up.

def bfs(initial_state, goal_state, verbose=True):
    """
    Breadth-first search. Returns (goal_node, nodes_expanded) or (None, nodes_expanded).
    """
    state_space.clear()
    root = Node(initial_state)
    if initial_state == goal_state:
        return root, 0

    frontier = deque([root])          # FIFO queue
    visited = {initial_state}         # states already discovered
    expanded = 0
    current_level = 0

    while frontier:
        node = frontier.popleft()     # take from the FRONT
        if verbose and node.depth != current_level:
            current_level = node.depth
            print(f"  finished level {current_level - 1}: frontier now holds {len(frontier) + 1} nodes")
        expanded += 1

        for action, next_state, cost in expand(node.state):
            if next_state in visited:
                continue
            visited.add(next_state)
            child = Node(next_state, node, action, node.depth + 1, node.path_cost + cost)
            if next_state == goal_state:      # goal test when generated (still optimal for BFS)
                return child, expanded
            frontier.append(child)            # add to the BACK
    return None, expanded


# Output

ACTION_NAMES = {"W": "Up", "A": "Left", "X": "Down", "D": "Right"}

def board_str(state):
    lines = []
    for r in range(3):
        lines.append(" ".join(" " if v == 0 else str(v) for v in state[r * 3:r * 3 + 3]))
    return "\n".join("  " + l for l in lines)

def print_solution(goal_node):
    path = goal_node.path()
    for node in path:
        if node.depth == 0:
            print("\nRoot Node (Level 0)")
        else:
            print(f"\nLevel {node.depth}  (blank moved {ACTION_NAMES[node.action]}, '{node.action}')")
        print(board_str(node.state))
    print(f"\nTotal number of moves to reach the goal state = {goal_node.depth}")
    print("Move sequence:", " ".join(n.action for n in path[1:]) or "(none)")

def solve(initial_state, goal_state):
    validate_state(initial_state, "initial state")
    validate_state(goal_state, "goal state")
    if not is_solvable(initial_state, goal_state):
        print("This puzzle is UNSOLVABLE: the goal is not reachable from the initial state.")
        return None
    goal_node, expanded = bfs(initial_state, goal_state)
    if goal_node is None:
        print("No solution found.")
        return None
    print_solution(goal_node)
    print(f"Nodes expanded: {expanded} | States stored in state_space: {len(state_space)}")
    return goal_node


# Main

# ==============================================================================
# PART 3 - the GUI, where the two parts work together
#
# The board here is the same tuple of nine ints, so to_game() and from_game() are
# straight copies: in one file the game and the search already share one board form.
# ==============================================================================

STEP_MS = 550                                   # how long a BFS step stays on screen
DEFAULT_INITIAL = (1, 5, 2, 7, 4, 3, 8, 6, 0)   # the handout board: 8 moves away
INPUT_EXAMPLE = "[1, 5, 2, 7, 4, 3, 8, 6, ' ']"

# The tile that moves when a tile next to the blank is clicked. The key names the
# direction the BLANK moves, because that is what the lab sheet's keys mean.
CLICK_KEYS = {1: 'D', -1: 'A', -3: 'W', 3: 'X'}

# One file now, so the blank token is the same everywhere. to_game() and
# from_game() are kept because Part 3 is written against them.
GAME_BLANK = BLANK

# ------------------------------------------------------------------ look of the app
# Tk only sees the fonts that fontconfig exposes to it, and on this machine that list
# is short: Nunito, JetBrains Mono and Cantarell are installed but Tk does not offer
# them, so asking for one silently falls back to a serif-ish default. The first family
# from this list that Tk really has is used for everything, and all of it is sans serif.
UI_FONT_CHOICES = ("Liberation Sans", "Nimbus Sans L", "DejaVu Sans", "Helvetica", "Arial")
FALLBACK_FONT = "TkDefaultFont"

INK = "#1f2933"                 # main text
MUTED = "#6b7280"               # secondary text
BG = "#f4f5f7"                  # window background
CARD = "#ffffff"                # panels
LINE = "#e3e6ea"                # hairlines
TILE = "#ffffff"
TILE_EDGE = "#e4e8ed"
TILE_HOVER = "#eef4ff"          # a tile the player can move
TILE_MOVED = "#3b82f6"          # the tile that just moved
TILE_INK_MOVED = "#ffffff"
HOLE = "#e9ecf0"                # the empty space
PRIMARY = "#23272f"             # main button
PRIMARY_HOVER = "#3a4048"
GHOST = "#e9ecf1"               # secondary button
GHOST_HOVER = "#dde2e9"
OFF = "#e3e6ea"                 # disabled button
OK = "#1a7f37"
BAD = "#b42318"

TILE_SIZE = 104
TILE_GAP = 10
BOARD_PAD = 14


def to_game(board):
    """Search board -> whatever the game file's functions expect."""
    if GAME_BLANK == 0:
        return tuple(board)
    return [GAME_BLANK if value == BLANK else value for value in board]


def from_game(state):
    """Whatever the game file hands back -> search board."""
    if GAME_BLANK == 0:
        return tuple(state)
    return tuple(BLANK if value == GAME_BLANK else value for value in state)


def game_moves(board):
    """The legal moves from a board, taken from the game's own generator.

    The game answers with {key: board} and the search with [(key, board), ...], so
    both are read into a dict here.
    """
    return {key: from_game(value)
            for key, value in dict(get_possible_moves(to_game(board))).items()}


def search_moves(board):
    """The same thing from the search's generator, for the check below."""
    return dict(get_possible_moves(board))


def rules_agree(board):
    """True when the game and the search list the same legal moves for a board."""
    return sorted(game_moves(board)) == sorted(search_moves(board))


def parse_board(text):
    """Read a board typed as [1, 2, 3, 4, ' ', 8, 5, 6, 7]. Raises ValueError."""
    text = text.strip()
    if not text:
        raise ValueError("type a board first")
    try:
        items = ast.literal_eval(text)
    except (ValueError, SyntaxError):
        raise ValueError(f"use the format {INPUT_EXAMPLE}")
    if not isinstance(items, (list, tuple)) or len(items) != SIZE * SIZE:
        raise ValueError("a board has exactly nine cells")
    board = []
    for item in items:
        if isinstance(item, str) and item.strip() in ('', '_'):
            board.append(BLANK)
        elif isinstance(item, int) and not isinstance(item, bool):
            board.append(item)
        else:
            raise ValueError(f"{item!r} is not a tile number or a blank")
    board = tuple(board)
    if sorted(board) != list(range(SIZE * SIZE)):
        raise ValueError("use the tiles 1 to 8 once each plus one blank")
    return board


def key_for_click(board, index):
    """Which key slides the tile at `index`, or None when that tile cannot move."""
    blank = board.index(BLANK)
    difference = index - blank
    if difference in (1, -1) and blank // SIZE != index // SIZE:
        return None                 # the row wrapped, so the tile is not next to it
    return CLICK_KEYS.get(difference)


def pick_font(preferred, fallback=FALLBACK_FONT):
    """The first font family in `preferred` that Tk can actually use."""
    available = {name.lower() for name in tkfont.families()}
    for name in preferred:
        if name.lower() in available:
            return name
    return fallback


def rounded_box(canvas, x1, y1, x2, y2, radius, **options):
    """A rounded rectangle: Tkinter has none, so the outline is a smoothed polygon
    through the corner points."""
    points = [x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
              x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
              x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1]
    return canvas.create_polygon(points, smooth=True, **options)


class PuzzleGUI:
    """The window. The play/solve state lives here so the checks can drive it."""

    def __init__(self, root):
        self.root = root
        self.initial = DEFAULT_INITIAL
        self.goal = DEFAULT_GOAL
        self.board = DEFAULT_INITIAL
        self.player_moves = []
        self.optimal = None             # the BFS answer for this start
        self.optimal_moves = []
        self.replay_index = 0
        self.replay_boards = []         # the boards the animation has shown
        self.replay_job = None
        self.solved = False

        root.title("8-Puzzle - play it, then watch BFS solve it")
        root.configure(bg=BG)
        root.resizable(False, False)
        self.ui_font = pick_font(UI_FONT_CHOICES)
        self.button_kinds = {}          # so the flat buttons can be switched on and off

        self._build_widgets()
        # Ask the window how tall the content is instead of guessing a height, so the
        # log card is never pushed off the bottom.
        root.update_idletasks()
        root.geometry(f"560x{root.winfo_reqheight() + 24}+30+20")
        self._bind_keys()
        self.new_game()

    # ------------------------------------------------------------------ widgets
    def _build_widgets(self):
        """Build the window once; everything that changes is redrawn in refresh_board."""
        head = tk.Frame(self.root, bg=BG)
        head.pack(fill="x", padx=26, pady=(16, 0))
        tk.Label(head, text="8-Puzzle", font=(self.ui_font, 24, "bold"), bg=BG, fg=INK).pack(anchor="w")
        tk.Label(head, text="Play it yourself, then watch breadth-first search solve it",
                 font=(self.ui_font, 11), bg=BG, fg=MUTED).pack(anchor="w")
        tk.Label(head, justify="left", font=(self.ui_font, 10), bg=BG, fg=MUTED, wraplength=500,
                 text=("Tiles 1-8 and one empty space. Click a tile next to the space, or move "
                       "the space with W (up), A (left), X (down), D (right) or the arrow keys.")).pack(
            anchor="w", pady=(8, 0))

        inputs = tk.Frame(self.root, bg=CARD, highlightbackground=LINE, highlightthickness=1)
        inputs.pack(fill="x", padx=26, pady=(14, 0))
        tk.Label(inputs, text="INITIAL STATE", font=(self.ui_font, 8, "bold"), bg=CARD, fg=MUTED).grid(
            row=0, column=0, sticky="w", padx=(14, 8), pady=(12, 2))
        self.initial_var = tk.StringVar(value=INPUT_EXAMPLE)
        self._entry(inputs, self.initial_var).grid(row=1, column=0, sticky="w", padx=(14, 8))
        tk.Label(inputs, text="GOAL STATE", font=(self.ui_font, 8, "bold"), bg=CARD, fg=MUTED).grid(
            row=0, column=1, sticky="w", padx=(8, 14), pady=(12, 2))
        self.goal_var = tk.StringVar(value="[1, 2, 3, 4, 5, 6, 7, 8, ' ']")
        self._entry(inputs, self.goal_var).grid(row=1, column=1, sticky="w", padx=(8, 14))
        # The button goes under the two boxes: next to them the row is wider than the
        # window and the label gets cut off.
        self.new_game_button = self._button(inputs, "New game", self.read_entries_and_start,
                                            kind="primary")
        self.new_game_button.grid(row=2, column=0, columnspan=2, sticky="e", padx=(0, 14),
                                  pady=(12, 14))

        # the board
        side = SIZE * TILE_SIZE + (SIZE - 1) * TILE_GAP + 2 * BOARD_PAD
        self.board_canvas = tk.Canvas(self.root, width=side, height=side, bg=BG,
                                      highlightthickness=0, cursor="arrow")
        self.board_canvas.pack(pady=(14, 4))
        self.board_canvas.bind("<Button-1>", self.on_board_click)
        self.board_canvas.bind("<Motion>", self.on_board_hover)
        self.cell_boxes = []
        self.tile_shapes = []
        self.tile_labels = []
        for index in range(SIZE * SIZE):
            row, col = divmod(index, SIZE)
            x1 = BOARD_PAD + col * (TILE_SIZE + TILE_GAP)
            y1 = BOARD_PAD + row * (TILE_SIZE + TILE_GAP)
            self.cell_boxes.append((x1, y1, x1 + TILE_SIZE, y1 + TILE_SIZE))
            rounded_box(self.board_canvas, x1, y1 + 3, x1 + TILE_SIZE, y1 + TILE_SIZE + 3,
                        18, fill="#e8ebef", outline="")                     # soft shadow
            shape = rounded_box(self.board_canvas, x1, y1, x1 + TILE_SIZE, y1 + TILE_SIZE,
                                18, fill=TILE, outline=TILE_EDGE, width=1)
            label = self.board_canvas.create_text(x1 + TILE_SIZE / 2, y1 + TILE_SIZE / 2 - 2,
                                                  text="", font=(self.ui_font, 30, "bold"), fill=INK)
            self.tile_shapes.append(shape)
            self.tile_labels.append(label)

        # status line with a coloured bar next to it
        status_row = tk.Frame(self.root, bg=BG)
        status_row.pack(fill="x", padx=26, pady=(6, 0))
        self.status_accent = tk.Frame(status_row, bg=LINE, width=3, height=36)
        self.status_accent.pack(side="left", fill="y", padx=(0, 10))
        self.status = tk.Label(status_row, text="", bg=BG, fg=INK, font=(self.ui_font, 11, "bold"),
                               wraplength=460, justify="left", anchor="w")
        self.status.pack(side="left", fill="x", expand=True)

        # buttons
        row = tk.Frame(self.root, bg=BG)
        row.pack(fill="x", padx=26, pady=(12, 0))
        self.solve_button = self._button(row, "Show the optimal solution (BFS)", self.show_optimal,
                                         kind="primary", state="disabled")
        self.solve_button.pack(side="left")
        self.stop_button = self._button(row, "Stop", self.stop_replay, kind="ghost", state="disabled")
        self.stop_button.pack(side="left", padx=8)
        self.give_up_button = self._button(row, "Give up", self.give_up, kind="ghost")
        self.give_up_button.pack(side="left")

        # play log
        log_card = tk.Frame(self.root, bg=CARD, highlightbackground=LINE, highlightthickness=1)
        log_card.pack(fill="both", expand=True, padx=26, pady=(12, 16))
        tk.Label(log_card, text="PLAY LOG", font=(self.ui_font, 8, "bold"), bg=CARD, fg=MUTED).pack(
            anchor="w", padx=14, pady=(10, 0))
        self.log = tk.Text(log_card, height=5, font=(self.ui_font, 9), bg=CARD, fg=INK,
                           relief="flat", highlightthickness=0, borderwidth=0, wrap="word",
                           state="disabled")
        self.log.pack(fill="both", expand=True, padx=14, pady=(4, 12))

    def _entry(self, parent, variable):
        """A flat entry with a hairline border, which the default Tk entry does not have."""
        return tk.Entry(parent, textvariable=variable, width=27, font=(self.ui_font, 10),
                        bg=CARD, fg=INK, relief="flat", highlightthickness=1,
                        highlightbackground=LINE, highlightcolor=TILE_MOVED, insertbackground=INK)

    def _button(self, parent, text, command, kind="ghost", state="normal"):
        """One flat button. `kind` picks the colours; disabled buttons are set in _enable."""
        background, foreground, hover = {"primary": (PRIMARY, "#ffffff", PRIMARY_HOVER),
                                         "ghost": (GHOST, INK, GHOST_HOVER)}[kind]
        button = tk.Button(parent, text=text, command=command, font=(self.ui_font, 10, "bold"),
                           bg=background, fg=foreground, activebackground=hover,
                           activeforeground=foreground, disabledforeground="#9aa1ab",
                           relief="flat", borderwidth=0, padx=14, pady=7, cursor="hand2")
        self.button_kinds[button] = kind
        self._enable(button, state == "normal")
        return button

    def _enable(self, button, enabled):
        """Switch a button on or off. Tk only greys the text of a disabled button, so
        the fill is set here as well."""
        background = {"primary": PRIMARY, "ghost": GHOST}[self.button_kinds.get(button, "ghost")]
        button.config(state="normal" if enabled else "disabled",
                      bg=background if enabled else OFF)

    def _bind_keys(self):
        for key in "WAXD":
            self.root.bind(f"<{key.lower()}>", lambda event, k=key: self.play(k))
            self.root.bind(f"<{key}>", lambda event, k=key: self.play(k))
        self.root.bind("<Up>", lambda event: self.play('W'))
        self.root.bind("<Down>", lambda event: self.play('X'))
        self.root.bind("<Left>", lambda event: self.play('A'))
        self.root.bind("<Right>", lambda event: self.play('D'))

    # ------------------------------------------------------------------- play
    def new_game(self, initial=None, goal=None):
        """Start again from these two boards (or from the ones already set)."""
        self.stop_replay()
        if initial is not None:
            self.initial = tuple(initial)
        if goal is not None:
            self.goal = tuple(goal)
        self.board = self.initial
        self.player_moves = []
        self.optimal = None
        self.optimal_moves = []
        self.replay_index = 0
        self.replay_boards = []
        self.solved = self.board == self.goal
        self._enable(self.solve_button, False)
        self._enable(self.stop_button, False)
        self.clear_log()
        self.write_log(f"initial board  {self.initial}")
        self.write_log(f"goal board     {self.goal}")
        if not is_solvable(to_game(self.initial), to_game(self.goal)):
            self.write_log("this board can never reach that goal (parity mismatch)")
            self.set_status("Unsolvable pair - type another board.", BAD)
            self.in_play = False
        elif self.solved:
            self.in_play = False
            self.write_log("the initial board already is the goal board")
            self.set_status("Already solved: 0 moves. Press 'Show the optimal solution'.", OK)
            self._enable(self.solve_button, True)
        else:
            self.in_play = True
            self.set_status("Your move - 0 moves so far.", INK)
        self.refresh_board()
        if not rules_agree(self.board):
            self.write_log("warning: the game and the search do not list the same moves here")
        return self.in_play

    def read_entries_and_start(self):
        """Take the two boards from the entry boxes and start a game."""
        try:
            initial = parse_board(self.initial_var.get())
            goal = parse_board(self.goal_var.get())
        except ValueError as error:
            self.set_status(f"Cannot read that board: {error}", BAD)
            return False
        if initial == goal:
            self.set_status("The two boards are the same, so there is nothing to solve.", BAD)
            return False
        return self.new_game(initial, goal)

    def click_tile(self, index):
        """Slide the clicked tile, if it is next to the blank."""
        key = key_for_click(self.board, index)
        if key is None:
            self.set_status("That tile is not next to the empty space.", BAD)
            return False
        return self.play(key)

    def on_board_click(self, event):
        """Turn a click on the canvas into the cell under the pointer."""
        index = self.cell_at(event.x, event.y)
        if index is None:
            return False
        return self.click_tile(index)

    def on_board_hover(self, event):
        """A hand and a light tile when the pointer is over a tile the player can move."""
        index = self.cell_at(event.x, event.y)
        movable = index is not None and key_for_click(self.board, index) is not None
        self.board_canvas.config(cursor="hand2" if movable else "arrow")
        if self.replay_job is None:
            self.refresh_board(hover=index if movable else None)

    def cell_at(self, x, y):
        """Which cell holds this point, or None when the point is between the tiles."""
        for index, (x1, y1, x2, y2) in enumerate(self.cell_boxes):
            if x1 <= x <= x2 and y1 <= y <= y2:
                return index
        return None

    def play(self, key):
        """Play one key through the game's own rules. Returns True when it moved."""
        if not getattr(self, "in_play", False) or self.solved or self.replay_job is not None:
            return False
        key = (key or "").upper()
        moves = game_moves(self.board)
        if key not in moves or not validate_move(to_game(self.board), key):
            self.set_status(f"'{key}' is not a legal move here.", BAD)
            self.write_log(f"refused        {key!r}")
            return False
        self.board = moves[key]
        self.player_moves.append(key)
        self.write_log(f"you            {key}   (move {len(self.player_moves)})")
        self.refresh_board(highlight=key)
        if self.board == self.goal:
            self.finish_player_game()
        else:
            self.set_status(f"Your move - {len(self.player_moves)} moves so far.", INK)
        return True

    def finish_player_game(self):
        """The player reached the goal, so work out BFS's answer and unlock it."""
        self.solved = True
        self.in_play = False
        node, expanded = bfs(self.initial, self.goal, verbose=False)
        if node is None:
            self.optimal_moves = []
            self.set_status("You solved it, but BFS found no route (check the boards).", BAD)
            return
        self.optimal = node
        self.optimal_moves = [step.action for step in node.path()[1:]]
        mine = len(self.player_moves)
        best = len(self.optimal_moves)
        if mine == best:
            verdict = f"Solved in {mine} moves - the optimal {best}. BFS agrees."
        else:
            verdict = (f"Solved in {mine} moves. BFS does it in {best} from the same board, "
                       f"so {mine - best} move(s) more.")
        self.set_status(verdict + "  Press 'Show the optimal solution'.", OK)
        self.write_log(f"solved         {mine} move(s) | BFS {best} move(s), {expanded} states expanded")
        self.write_log(f"BFS answer     {' '.join(self.optimal_moves) or '(none)'}")
        self._enable(self.solve_button, True)

    def give_up(self):
        """Let the player watch the answer without solving it themselves."""
        if self.solved:
            return False
        node, expanded = bfs(self.initial, self.goal, verbose=False)
        if node is None:
            self.set_status("BFS found no route, so this pair has no solution.", BAD)
            return False
        self.optimal = node
        self.optimal_moves = [step.action for step in node.path()[1:]]
        self.in_play = False
        self.write_log(f"gave up        after {len(self.player_moves)} move(s) | "
                       f"BFS {len(self.optimal_moves)} move(s), {expanded} states expanded")
        self.set_status(f"BFS needs {len(self.optimal_moves)} moves from here. "
                        "Press 'Show the optimal solution'.", INK)
        self._enable(self.solve_button, True)
        return True

    # ---------------------------------------------------------------- replay
    def show_optimal(self):
        """Play BFS's answer from the initial board, one move at a time."""
        if self.optimal is None:
            node, _ = bfs(self.initial, self.goal, verbose=False)
            if node is None:
                self.set_status("BFS found no route for this pair.", BAD)
                return False
            self.optimal = node
            self.optimal_moves = [step.action for step in node.path()[1:]]
        self.replay_index = 0
        self.replay_boards = []
        self.board = self.initial
        self.refresh_board()
        self.write_log(f"showing BFS    {len(self.optimal_moves)} moves from the start board")
        self._enable(self.stop_button, True)
        # The start board stays on screen for one step before the first move, so the
        # player can see the board the answer is measured from.
        self.replay_job = self.root.after(STEP_MS, self.step_replay)
        return True

    def step_replay(self):
        """One step of the animation. Schedules the next one."""
        if self.replay_index >= len(self.optimal_moves):
            self.replay_job = None
            self._enable(self.stop_button, False)
            self.board = self.goal
            self.refresh_board()
            self.set_status(f"BFS solved it in {len(self.optimal_moves)} moves: "
                            f"{' '.join(self.optimal_moves) or '(none)'}", OK)
            return False
        key = self.optimal_moves[self.replay_index]
        self.board = game_moves(self.board)[key]
        self.replay_index += 1
        self.replay_boards.append(self.board)
        self.refresh_board(highlight=key)
        self.set_status(f"BFS move {self.replay_index} of {len(self.optimal_moves)}: '{key}'"
                        f"   ({len(self.player_moves)} of yours)", MUTED)
        self.replay_job = self.root.after(STEP_MS, self.step_replay)
        return True

    def stop_replay(self):
        """Stop the animation where it is."""
        if self.replay_job is not None:
            self.root.after_cancel(self.replay_job)
            self.replay_job = None
            self._enable(self.stop_button, False)
            self.refresh_board()
            self.write_log(f"replay stopped at move {self.replay_index}")
        return True

    # ----------------------------------------------------------------- output
    def refresh_board(self, highlight=None, hover=None):
        """Draw the board. `highlight` is the key just played, `hover` a cell under the mouse."""
        moved = self.previous_cell(highlight) if highlight else None
        for index, value in enumerate(self.board):
            shape = self.tile_shapes[index]
            label = self.tile_labels[index]
            if index == moved:
                fill, ink, edge, text = TILE_MOVED, TILE_INK_MOVED, TILE_MOVED, str(value)
            elif value == BLANK:
                fill, ink, edge, text = HOLE, MUTED, HOLE, ""
            elif index == hover:
                fill, ink, edge, text = TILE_HOVER, INK, TILE_MOVED, str(value)
            else:
                fill, ink, edge, text = TILE, INK, TILE_EDGE, str(value)
            self.board_canvas.itemconfig(shape, fill=fill, outline=edge)
            self.board_canvas.itemconfig(label, text=text, fill=ink)

    def drawn_board(self):
        """What the board shows on screen, for the checks and for any screenshot check."""
        return [self.board_canvas.itemcget(label, "text") for label in self.tile_labels]

    def previous_cell(self, key):
        """The cell the blank came from, for the highlight. The key is the blank's move."""
        blank = self.board.index(BLANK)
        step = {'W': SIZE, 'A': 1, 'X': -SIZE, 'D': -1}[key]
        previous = blank + step
        return previous if 0 <= previous < SIZE * SIZE else None

    def set_status(self, text, colour=INK):
        self.status.config(text=text, fg=colour)
        self.status_accent.config(bg=colour)

    def write_log(self, text):
        self.log.config(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def clear_log(self):
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        self.log.config(state="disabled")


def main():
    try:
        root = tk.Tk()
    except tk.TclError as error:
        sys.exit(f"No window available ({error}). Run this from a desktop session.")
    PuzzleGUI(root)
    root.mainloop()
# ==============================================================================
# PART 4 - the menu
# ==============================================================================

def main_menu():
    """The entry point: play the game, run the search on a file, or open the GUI."""
    describe_bfs()
    print("DS 170 / CMSC 170 - Laboratory Exercise No. 3")
    print("  1 - play the 8-puzzle game (Task 2)")
    print("  2 - solve a board from a file with BFS (Task 3)")
    print("  3 - open the GUI: play it first, then watch BFS solve it")
    print("  Q - quit")
    for attempt in range(3):
        choice = input("\nChoice: ").strip().upper()
        if choice == 'Q':
            print("Goodbye.")
            return
        if choice == '1':
            play()
            return
        if choice == '2':
            path = input("Path to input file (e.g. sample_8_moves.txt): ").strip()
            try:
                initial_state, goal_state = parse_state_file(path)
            except (OSError, ValueError) as error:
                print(f"Could not read input: {error}")
                return
            print("Initial state:\n" + board_str(initial_state))
            print("Goal state:\n" + board_str(goal_state))
            print("\nSearching...")
            solve(initial_state, goal_state)
            return
        if choice == '3':
            main()
            return
        print("Type 1, 2, 3 or Q.")
    print("No valid choice, stopping.")


if __name__ == "__main__":
    main_menu()
