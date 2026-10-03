"""
DS 170 / CMSC 170 - Laboratory Exercise No. 3
GUI for the 8-puzzle: solve the puzzle yourself, then watch BFS solve it.

How it works
------------
Type an initial board and a goal board, then play with the mouse or the keyboard.
The move rules and the move validator come from Task2_Lab3.py, so the GUI plays by
the same rules as the text game. Clicking a tile next to the empty space slides it;
the keys W, A, X and D move the empty space (up, left, down, right) exactly as the
lab sheet defines them.

When the player reaches the goal, the "Show the optimal solution" button wakes up.
It runs the Task 3 BFS from the board the player started with and replays that
answer one move at a time, so the player can compare their own count with BFS's.
Before the puzzle is solved the button is off, which is the order the lab asks for:
solve it first, then look at the optimal answer.

Run it from the folder that holds the two program files:

    python3 gui_8puzzle.py

A desktop session is needed. Over SSH it stops with "no display name and no
$DISPLAY environment variable".

The board is drawn on a canvas rather than with buttons: a button brings the old Tk
look with it (thick borders, grey slabs) and the tile spacing is easier to control by
drawing. The colours and the two fonts are set once in the constants below.

Board form
----------
Everything in this file uses the search's board: a tuple of nine ints, 0 for the
blank. The game file writes a board its own way, so to_game() and from_game() are
the only two places that difference is handled. If the two files are moved onto one
board form later, those two functions become a straight copy and nothing else here
changes.
"""

import ast
import pathlib
import sys
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog

import Task2_Lab3 as game
import bfs_8puzzle as search

SIZE = 3
BLANK = 0
STEP_MS = 550                                   # how long a BFS step stays on screen
DEFAULT_INITIAL = (1, 5, 2, 7, 4, 3, 8, 6, 0)   # the handout board: 8 moves away
DEFAULT_GOAL = (1, 2, 3, 4, 5, 6, 7, 8, 0)      # Goal State A
INPUT_EXAMPLE = "[1, 5, 2, 7, 4, 3, 8, 6, ' ']"

# The tile that moves when a tile next to the blank is clicked. The key names the
# direction the BLANK moves, because that is what the lab sheet's keys mean.
CLICK_KEYS = {1: 'D', -1: 'A', -3: 'W', 3: 'X'}

# The game's blank token. The two files were written separately: the first version of
# the game used ' ' and a list, the search uses 0 and a tuple. to_game() and
# from_game() are the only place that shows.
GAME_BLANK = getattr(game, "BLANK", " ")

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

TILE_SIZE = 92
TILE_GAP = 10
BOARD_PAD = 14


HERE = pathlib.Path(__file__).resolve().parent


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
            for key, value in dict(game.get_possible_moves(to_game(board))).items()}


def search_moves(board):
    """The same thing from the search's generator, for the check below."""
    return dict(search.get_possible_moves(board))


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
    """The window. The play/solve state lives here so the checks can drive it.

    Two modes, one window: in "game" mode the optimal-solution button stays off until
    the player solves the puzzle, and in "bfs" mode the search is the point of the
    window, so the button is ready straight away.
    """

    def __init__(self, root, mode="game"):
        self.root = root
        self.mode = mode
        self.initial = DEFAULT_INITIAL
        self.goal = DEFAULT_GOAL
        self.board = DEFAULT_INITIAL
        self.player_moves = []
        self.optimal = None             # the BFS answer for this start
        self.optimal_moves = []
        self.optimal_expanded = None
        self.replay_index = 0
        self.replay_boards = []         # the boards the animation has shown
        self.replay_job = None
        self.solved = False
        self.gave_up = False
        self.bfs_explained = False

        root.title("8-Puzzle")
        root.configure(bg=BG)
        root.resizable(False, False)
        self.ui_font = pick_font(UI_FONT_CHOICES)
        self.button_kinds = {}          # so the flat buttons can be switched on and off

        self._build_widgets()
        self.set_mode(mode)
        self.resize_to_content()
        root.geometry("+30+20")
        self._bind_keys()
        self.new_game()

    # ------------------------------------------------------------------ widgets
    def _build_widgets(self):
        """Build the window once; everything that changes is redrawn in refresh_board."""
        head = tk.Frame(self.root, bg=BG)
        head.pack(fill="x", padx=26, pady=(16, 0))
        tk.Label(head, text="8-Puzzle", font=(self.ui_font, 24, "bold"), bg=BG, fg=INK).pack(anchor="w")
        self.subtitle = tk.Label(head, text="", font=(self.ui_font, 11), bg=BG, fg=MUTED)
        self.subtitle.pack(anchor="w")

        # Which task the window is for. This used to be a question in the terminal, which
        # made no sense once the window was open: it is a click here.
        toggle = tk.Frame(head, bg=BG)
        toggle.pack(anchor="w", pady=(10, 0))
        self.mode_buttons = {}
        for key, text in (("game", "Play the puzzle (Task 2)"),
                          ("bfs", "Solve with BFS (Task 3)")):
            button = self._button(toggle, text, lambda chosen=key: self.set_mode(chosen),
                                  kind="primary")
            button.pack(side="left", padx=(0, 8))
            self.mode_buttons[key] = button

        # The explanation itself, in the same words the CLI prints. The card folds away
        # when the player does not need it, so the window can be short.
        self.about_card = tk.Frame(self.root, bg=CARD, highlightbackground=LINE,
                                   highlightthickness=1)
        self.about_card.pack(fill="x", padx=26, pady=(12, 0))
        self.about_open = False
        self.about_toggle = tk.Button(self.about_card, text="", command=self.toggle_about,
                                      font=(self.ui_font, 8, "bold"), bg=CARD, fg=MUTED,
                                      activebackground=CARD, activeforeground=INK,
                                      relief="flat", borderwidth=0, cursor="hand2",
                                      anchor="w", padx=14, pady=8)
        self.about_toggle.pack(fill="x")
        # Folded away until it is asked for: the title row says it is there.
        self.about_body = tk.Frame(self.about_card, bg=CARD)
        self.about = tk.Text(self.about_body, height=13, font=(self.ui_font, 9), bg=CARD, fg=INK,
                             relief="flat", highlightthickness=0, borderwidth=0, wrap="word",
                             state="disabled")
        self.about.pack(side="left", fill="both", expand=True, padx=(14, 0), pady=(0, 12))
        scroll = tk.Scrollbar(self.about_body, command=self.about.yview, width=12)
        scroll.pack(side="right", fill="y", pady=(0, 12), padx=(0, 10))
        self.about.config(yscrollcommand=scroll.set)

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
        tools = tk.Frame(inputs, bg=CARD)
        tools.grid(row=2, column=0, sticky="w", padx=(14, 0), pady=(12, 14))
        self.random_button = self._button(tools, "Random board", self.random_board, kind="ghost")
        self.random_button.pack(side="left")
        self.load_button = self._button(tools, "Load from file", self.load_from_file, kind="ghost")
        self.load_button.pack(side="left", padx=8)
        self.new_game_button = self._button(inputs, "New game", self.read_entries_and_start,
                                            kind="primary")
        self.new_game_button.grid(row=2, column=1, sticky="e", padx=(0, 14), pady=(12, 14))

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
        # In game mode the first thing on offer is getting unstuck: "Give up" works
        # straight away and unlocks the animation, instead of a greyed-out button the
        # player cannot use yet.
        self.give_up_button = self._button(row, "Give up - show the answer", self.give_up,
                                           kind="ghost")
        self.solve_button = self._button(row, "Show the optimal solution (BFS)", self.show_optimal,
                                         kind="primary", state="disabled")
        self.solve_button.pack(side="left")
        self.stop_button = self._button(row, "Stop", self.stop_replay, kind="ghost", state="disabled")
        self.stop_button.pack(side="left", padx=8)

        # play log
        log_card = tk.Frame(self.root, bg=CARD, highlightbackground=LINE, highlightthickness=1)
        log_card.pack(fill="x", padx=26, pady=(12, 16))
        tk.Label(log_card, text="PLAY LOG", font=(self.ui_font, 8, "bold"), bg=CARD, fg=MUTED).pack(
            anchor="w", padx=14, pady=(10, 0))
        self.log = tk.Text(log_card, height=4, font=(self.ui_font, 9), bg=CARD, fg=INK,
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

    def set_mode(self, mode):
        """Switch the window between playing the puzzle and driving the search."""
        self.mode = mode
        for key, button in self.mode_buttons.items():
            active = key == mode
            background, ink = (PRIMARY, "#ffffff") if active else (GHOST, INK)
            button.config(bg=background, fg=ink, activebackground=background)
        if mode == "game":
            self.subtitle.config(text="Play it yourself, then watch breadth-first search solve it")
            self.show_description(game.GAME_DESCRIPTION)
        else:
            self.subtitle.config(text="Breadth-first search on the 8-puzzle: set a board, "
                                      "then watch it solved")
            self.show_description(search.BFS_DESCRIPTION)
        self.refresh_board()
        self.update_buttons()

    def toggle_about(self):
        """Fold the description away, or open it again, and resize the window to fit."""
        self.about_open = not self.about_open
        if self.about_open:
            self.about_body.pack(fill="both", expand=True)
        else:
            self.about_body.pack_forget()
        self.update_about_title()
        self.resize_to_content()

    def update_about_title(self):
        """The card's title, with an arrow showing whether it is open."""
        name = "HOW TO PLAY" if self.mode == "game" else "ABOUT THIS MODE"
        arrow = "v" if self.about_open else ">"
        self.about_toggle.config(text=f"{arrow}  {name}   (click to "
                                      f"{'hide' if self.about_open else 'show'})")

    def resize_to_content(self):
        """Ask the window how tall its content is instead of guessing."""
        self.root.update_idletasks()
        self.root.geometry(f"560x{self.root.winfo_reqheight() + 24}")

    def show_description(self, text):
        """Put a description in the panel, scrolled back to the top."""
        self.about.config(state="normal")
        self.about.delete("1.0", "end")
        self.about.insert("1.0", text)
        self.about.config(state="disabled")
        self.about.yview_moveto(0.0)
        self.update_about_title()

    def update_buttons(self):
        """Button states for the mode and for how far the puzzle has got."""
        if not hasattr(self, "solve_button"):
            return
        self._enable(self.solve_button, self.mode == "bfs" or self.solved or self.gave_up)
        if self.mode == "game":
            self.give_up_button.pack(side="left", padx=(0, 8), before=self.solve_button)
        else:
            self.give_up_button.pack_forget()

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
        self.optimal_expanded = None
        self.replay_index = 0
        self.replay_boards = []
        self.solved = self.board == self.goal
        self.gave_up = False
        self._enable(self.solve_button, False)
        self._enable(self.stop_button, False)
        self.clear_log()
        self.write_log(f"initial board  {self.initial}")
        self.write_log(f"goal board     {self.goal}")
        if not game.is_solvable(to_game(self.initial), to_game(self.goal)):
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
            self.set_status("Your move - 0 moves so far. Solve it, or press 'Give up - show "
                            "the answer'.", INK)
        self.refresh_board()
        if not rules_agree(self.board):
            self.write_log("warning: the game and the search do not list the same moves here")
        if self.mode == "bfs" and self.in_play:
            # In this mode the search is the point of the window, so the answer is
            # offered straight away instead of after the player solves the puzzle.
            self.set_status("BFS mode - press 'Show the optimal solution (BFS)' to watch the "
                            "search from this board.", INK)
        self.update_buttons()
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

    def random_board(self):
        """Put a random board in the window, solvable to the goal in the box."""
        try:
            goal = parse_board(self.goal_var.get())
        except ValueError:
            goal = self.goal
        board = game.random_state(goal)
        started = self.new_game(board, goal)
        # new_game() clears the log, so the line about the board goes in afterwards.
        self.write_log(f"random board   {board}")
        return started

    def load_from_file(self, path=None):
        """Read the two boards from an input file, the Task 3 format.

        The checks call this with a path; the button asks for the file first.
        """
        if path is None:
            path = filedialog.askopenfilename(title="Open a board file",
                                              initialdir=str(HERE),
                                              filetypes=[("Board files", "*.txt"),
                                                         ("All files", "*")])
            if not path:
                return False
        try:
            initial, goal = search.parse_state_file(path)
        except (OSError, ValueError) as error:
            self.set_status(f"Cannot read that file: {error}", BAD)
            self.write_log(f"file refused   {error}")
            return False
        self.write_log(f"file loaded    {pathlib.Path(path).name}")
        started = self.new_game(initial, goal)
        # new_game() clears the log, so the file line is written after it.
        self.write_log(f"loaded from    {pathlib.Path(path).name}")
        return started

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
        if key not in moves or not game.validate_move(to_game(self.board), key):
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
        node, expanded = search.bfs(self.initial, self.goal, verbose=False)
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
        node, expanded = search.bfs(self.initial, self.goal, verbose=False)
        if node is None:
            self.set_status("BFS found no route, so this pair has no solution.", BAD)
            return False
        self.optimal = node
        self.optimal_moves = [step.action for step in node.path()[1:]]
        self.in_play = False
        self.gave_up = True
        self.update_buttons()
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
            node, expanded = search.bfs(self.initial, self.goal, verbose=False)
            if node is None:
                self.set_status("BFS found no route for this pair.", BAD)
                return False
            self.optimal = node
            self.optimal_moves = [step.action for step in node.path()[1:]]
            self.optimal_expanded = expanded
            self.write_log(f"BFS answer     {len(self.optimal_moves)} move(s), "
                           f"{expanded} states expanded")
            self.write_log(f"BFS sequence   {' '.join(self.optimal_moves) or '(none)'}")
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


def main(mode="game"):
    """Open the window in "game" or "bfs" mode."""
    try:
        root = tk.Tk()
    except tk.TclError as error:
        sys.exit(f"No window available ({error}). Run this from a desktop session.")
    if mode == "bfs":
        search.describe_bfs()          # this mode is about the search, so it explains itself
    PuzzleGUI(root, mode=mode)
    root.mainloop()


if __name__ == "__main__":
    main()
