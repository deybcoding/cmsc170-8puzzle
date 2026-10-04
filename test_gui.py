"""
DS 170 / CMSC 170 - Laboratory Exercise No. 3
Member 3 - check battery for the GUI (gui_8puzzle.py).

This file is a test harness, not part of the program. It builds the real window,
keeps it hidden, and drives the same methods the buttons and keys call, so the
checks cover the play path, the click-to-move mapping, the "solve first, then show
the optimal solution" order, and the BFS answer itself.

Run it from the folder that holds gui_8puzzle.py, Task2_Lab3.py and bfs_8puzzle.py:

    python3 test_gui.py

Every line prints PASS or FAIL. The script exits with status 1 if anything failed.
A desktop session is needed because Tkinter wants a display, but the window stays
withdrawn so nothing pops up while the checks run.
"""

import pathlib
import sys
import time

import tkinter as tk

import gui_8puzzle as gui_module
from gui_8puzzle import PuzzleGUI, game_moves, key_for_click, parse_board, rules_agree

REPO = pathlib.Path(__file__).resolve().parent

GOAL = (1, 2, 3, 4, 5, 6, 7, 8, 0)
SAMPLE = (1, 5, 2, 7, 4, 3, 8, 6, 0)          # the handout board: 8 moves away
SOLUTION = list("AAWDWDXX")
UNSOLVABLE = (1, 2, 3, 4, 5, 6, 8, 7, 0)

results = []

def check(name, condition, detail=""):
    results.append((name, bool(condition)))
    print(f"  [{'PASS' if condition else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))
    return bool(condition)

def section(title):
    print(f"\n{title}")
    print("-" * len(title))

def pump(root, ms=15):
    """Run the event loop briefly so the animation timers actually fire."""
    root.after(ms, root.quit)
    root.mainloop()


# 0. Typed input.

section("0. Reading a typed board")

check("the lab sheet's format is read", parse_board("[1, 5, 2, 7, 4, 3, 8, 6, ' ']") == SAMPLE)
check("a blank typed as 0 is read too", parse_board("[1,2,3,4,0,5,6,7,8]") == (1, 2, 3, 4, 0, 5, 6, 7, 8))
check("a blank typed as '_' is read too", parse_board("[1,2,3,4,'_',5,6,7,8]") == (1, 2, 3, 4, 0, 5, 6, 7, 8))
for text, why in [("", "nothing typed"),
                  ("1 2 3 4 5 6 7 8", "not a list"),
                  ("[1, 2, 3, 4, 5, 6, 7, 8]", "eight cells"),
                  ("[1, 2, 3, 4, 5, 6, 7, 8, 8]", "a repeated tile"),
                  ("[1, 2, 3, 4, 5, 6, 7, 8, 9]", "a tile numbered 9"),
                  ("[1, 2, 3, 4, ' ', ' ', 6, 7, 8]", "two blanks")]:
    try:
        parse_board(text)
        check(f"refused: {why}", False, "accepted")
    except ValueError:
        check(f"refused: {why}", True)


# 1. Clicking a tile, and the keys.

section("1. Clicking a tile and the keys")

check("clicking the tile right of the blank moves the blank right",
      key_for_click((1, 2, 3, 4, 0, 5, 6, 7, 8), 5) == 'D')
check("clicking the tile left of the blank moves the blank left",
      key_for_click((1, 2, 3, 4, 0, 5, 6, 7, 8), 3) == 'A')
check("clicking the tile above the blank moves the blank up",
      key_for_click((1, 2, 3, 4, 0, 5, 6, 7, 8), 1) == 'W')
check("clicking the tile below the blank moves the blank down",
      key_for_click((1, 2, 3, 4, 0, 5, 6, 7, 8), 7) == 'X')
check("a tile on the edge of the board is not clicked through the row",
      key_for_click((1, 2, 3, 4, 5, 6, 7, 8, 0), 3) is None)
check("a tile far from the blank does nothing",
      key_for_click((1, 2, 3, 4, 0, 5, 6, 7, 8), 8) is None)

# Every board cell must map to exactly the keys the game itself allows.
mapping_ok = True
for blank_index in range(9):
    board = list(range(9))
    board[blank_index], board[0] = board[0], board[blank_index]     # put a blank anywhere
    board = tuple(board)
    clicked = {key_for_click(board, index) for index in range(9)
               if key_for_click(board, index) is not None}
    if clicked != set(game_moves(board)):
        mapping_ok = False
        print(f"         blank at {blank_index}: clicks {sorted(clicked)} "
              f"vs game moves {sorted(game_moves(board))}")
check("the clickable tiles are exactly the game's legal moves, at all nine cells", mapping_ok)


# 2. Playing, with the window hidden.

root = tk.Tk()
root.withdraw()
app = PuzzleGUI(root)

section("2. Playing the puzzle")

check("the app starts on the handout board", app.board == SAMPLE)
check("the optimal-solution button is off until the puzzle is solved",
      str(app.solve_button["state"]) == "disabled")

app.play('Z')
check("an unknown key is refused and does not move the board", app.board == SAMPLE
      and app.player_moves == [])

app.play('W')
check("a legal key moves the board the way the game's rules say",
      app.board == game_moves(SAMPLE)['W'])
check("the move counter goes up", app.player_moves == ['W'])
check("the board drawn on screen is the board in memory",
      app.drawn_board() == ["" if value == 0 else str(value) for value in app.board])

# A click on a tile that cannot move must not change anything.
app.click_tile(0)
check("clicking a tile away from the blank changes nothing",
      app.board == game_moves(SAMPLE)['W'] and app.player_moves == ['W'])

# Put the board back and solve it properly, checking every move through the game's
# own validator as we go.
app.new_game(SAMPLE, GOAL)
every_move_legal = True
for key in SOLUTION:
    before = app.board
    if not app.play(key) or app.board == before:
        every_move_legal = False
    if not gui_module.game.validate_move(gui_module.to_game(before), key):
        every_move_legal = False
check("every move in the player's solution passes the game's validator", every_move_legal)
check("the player's count is the 8 moves of the handout board", len(app.player_moves) == 8)
check("the board ends on the goal", app.board == GOAL)
check("the app knows the puzzle is solved", app.solved)
check("the app says which count is optimal",
      "optimal 8" in app.status["text"], app.status["text"][:70])

# The reveal only works once the solution is known.
section("3. The optimal solution after solving")

check("the reveal button is on now", str(app.solve_button["state"]) == "normal")
check("BFS's answer for this board is the 8 moves", app.optimal_moves == SOLUTION,
      " ".join(app.optimal_moves))

gui_module.STEP_MS = 1                    # do not wait 550 ms per step in the checks
check("pressing the button starts the replay", app.show_optimal())
check("the replay starts again from the board the player began with", app.board == SAMPLE)
check("the log says the BFS answer is being shown",
      "showing BFS" in app.log.get("1.0", "end"))

pumps = 0
while app.replay_job is not None and pumps < 40:
    pump(root)
    pumps += 1
check("the replay takes one step per move", len(app.replay_boards) == 8,
      f"{len(app.replay_boards)} steps")
check("the replay ends on the goal board", app.board == GOAL)
if app.optimal is None:
    check("the replay's boards are the boards BFS recorded", False, "no optimal node")
else:
    check("the replay's boards are the boards BFS recorded",
          app.replay_boards == [node.state for node in app.optimal.path()[1:]])
check("the animation stops on its own", app.replay_job is None)
check("the final message gives the number of moves",
      "BFS solved it in 8 moves" in app.status["text"], app.status["text"][:70])

# 4. Give up, and the boards that cannot be solved.

section("4. Giving up, and impossible boards")

app.new_game(SAMPLE, GOAL)
check("giving up finds the answer without solving",
      app.give_up() and app.optimal_moves == SOLUTION)
check("the reveal is available after giving up", str(app.solve_button["state"]) == "normal")

app.new_game(UNSOLVABLE, GOAL)
check("an impossible board is refused before play starts", app.in_play is False)
check("the app says the board cannot reach the goal",
      "Unsolvable" in app.status["text"], app.status["text"][:60])
app.play('D')
check("moves are ignored on an impossible board", app.board == UNSOLVABLE)

app.initial_var.set("[1, 2, 3, 4, 5, 6, 7, 8, ' ']")
app.goal_var.set("[1, 2, 3, 4, 5, 6, 7, 8, ' ']")
check("two identical boards are refused", app.read_entries_and_start() is False)
app.initial_var.set("not a board")
check("a board that cannot be read is refused", app.read_entries_and_start() is False)

app.new_game(GOAL, GOAL)
check("a board that is already the goal is accepted with 0 moves",
      app.solved and app.player_moves == [])
check("the reveal is available for an already solved board",
      str(app.solve_button["state"]) == "normal")


# 5. The game and the search, inside the GUI.

section("5. The GUI plays by the game's rules and solves with the search")

boards = [SAMPLE, GOAL, (1, 2, 3, 4, 0, 5, 6, 7, 8), (8, 6, 7, 2, 5, 4, 3, 0, 1)]
check("the game's moves and the search's moves agree on every test board",
      all(rules_agree(board) for board in boards))
check("the GUI's move generator and the game's generator give the same boards",
      all(game_moves(board) == {key: value for key, value in game_moves(board).items()}
          for board in boards))

app.new_game(SAMPLE, GOAL)
check("the GUI board is the board the search is given",
      gui_module.to_game(app.board) == gui_module.to_game(SAMPLE))

# A deep board: BFS from here is the 31-move answer, and the GUI must show that
# count rather than hanging.
start = time.perf_counter()
app.new_game((8, 6, 7, 2, 5, 4, 3, 0, 1), GOAL)
app.give_up()
elapsed = time.perf_counter() - start
check("the deepest board's answer is 31 moves", len(app.optimal_moves) == 31,
      f"{len(app.optimal_moves)} moves")
check("BFS through the GUI answers in a few seconds", elapsed < 20, f"{elapsed:.2f} s")


# 6. The keys are bound.

section("6. Key bindings")

bound = [key for key in ("w", "a", "x", "d", "W", "A", "X", "D", "Up", "Down", "Left", "Right")
         if root.bind(f"<{key}>")]
check("W A X D and the arrow keys are all bound", len(bound) == 12, f"{len(bound)} of 12")

app.new_game(SAMPLE, GOAL)
# A withdrawn window cannot take keyboard focus, so the window is shown for this one
# check and hidden again afterwards.
root.deiconify()
root.focus_force()
root.update()
root.event_generate("<w>", when="now")
pump(root, 60)
check("pressing 'w' plays the blank up through the key binding",
      app.player_moves == ['W'], f"moves: {app.player_moves}")
root.withdraw()


# 7. The two modes, and loading a board from a file.

section("7. BFS mode, and the file loader")

bfs_root = tk.Tk()
bfs_root.withdraw()
bfs_app = PuzzleGUI(bfs_root, mode="bfs")
check("the window opens in BFS mode", bfs_app.mode == "bfs")
check("there is a toggle button for each task", set(bfs_app.mode_buttons) == {"game", "bfs"})
check("the panel explains the search in this mode",
      "Breadth-First Search" in bfs_app.about.get("1.0", "end")
      and "ABOUT THIS MODE" in bfs_app.about_toggle.cget("text"))
check("the BFS description is folded away too", not bfs_app.about_open)
check("the optimal-solution button is ready straight away in BFS mode",
      str(bfs_app.solve_button["state"]) == "normal")
check("the window says which mode it is in", "BFS mode" in bfs_app.status["text"],
      bfs_app.status["text"][:50])
check("the puzzle can still be played in BFS mode", bfs_app.play('A') and bfs_app.player_moves == ['A'])

bfs_app.new_game(SAMPLE, GOAL)
check("the answer can be asked for without solving the puzzle first", bfs_app.show_optimal())
check("the working out is written into the log",
      "states expanded" in bfs_app.log.get("1.0", "end"))
check("the number of expanded states is kept", bfs_app.optimal_expanded is not None,
      f"{bfs_app.optimal_expanded} expanded")
check("the answer is the same 8 moves", bfs_app.optimal_moves == SOLUTION)
bfs_app.stop_replay()
bfs_root.destroy()

# The GUI's version of the Task 3 file option.
check("a board file can be loaded", app.load_from_file(str(REPO / "sample_8_moves.txt")))
check("the loaded boards are the file's boards", app.initial == SAMPLE and app.goal == GOAL)
check("the log names the file that was loaded",
      "sample_8_moves.txt" in app.log.get("1.0", "end"))
check("a file with a repeated tile is refused",
      app.load_from_file(str(REPO / "invalid_duplicate.txt")) is False)
check("a missing file is refused too",
      app.load_from_file(str(REPO / "not_here.txt")) is False)
check("the window says why the file was refused",
      "Cannot read that file" in app.status["text"], app.status["text"][:60])

# Switching task inside the window, which is what replaced the terminal question.
app.new_game(SAMPLE, GOAL)
app.set_mode("bfs")
check("clicking over to the search readies the button without solving anything",
      app.mode == "bfs" and str(app.solve_button["state"]) == "normal"
      and not app.solved)
check("the give-up button is gone in BFS mode", not app.give_up_button.winfo_ismapped())
app.set_mode("game")
check("clicking back to playing hides the search again until the puzzle is done",
      app.mode == "game" and str(app.solve_button["state"]) == "disabled")
app.give_up()
check("giving up from the game mode readies the button",
      str(app.solve_button["state"]) == "normal" and app.gave_up)
check("the panel explains how to play in game mode",
      "8-Puzzle Game Start" in app.about.get("1.0", "end")
      and "How a move works" in app.about.get("1.0", "end")
      and "HOW TO PLAY" in app.about_toggle.cget("text"))
check("the description starts folded away, out of the way",
      not app.about_open and app.about_body.winfo_manager() == "")
check("the folded row says there is a description to read",
      "(click to show)" in app.about_toggle.cget("text"))

# Opening it, and folding it away again: this is what keeps the window short.
short = app.root.winfo_reqheight()
app.toggle_about()
check("clicking the row opens the description",
      app.about_open and app.about_body.winfo_manager() == "pack"
      and app.root.winfo_reqheight() > short,
      f"{app.root.winfo_reqheight()} vs {short}")
check("the row now offers to hide it", "(click to hide)" in app.about_toggle.cget("text"))
app.toggle_about()
check("clicking again folds it away and the window shrinks back",
      not app.about_open and app.about_body.winfo_manager() == ""
      and app.root.winfo_reqheight() == short)
check("the description is the same text the CLI prints",
      app.about.get("1.0", "end").strip() == gui_module.game.GAME_DESCRIPTION.strip())

root.destroy()

# Summary.

failed = [name for name, ok in results if not ok]
print("\n" + "=" * 60)
print(f"Checks run: {len(results)}   Passed: {len(results) - len(failed)}   Failed: {len(failed)}")
if failed:
    print("\nFailed checks:")
    for name in failed:
        print(f"  - {name}")
print("=" * 60)
sys.exit(1 if failed else 0)
