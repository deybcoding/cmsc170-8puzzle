"""
DS 170 / CMSC 170 - Laboratory Exercise No. 3
Member 3 - check battery for the single submission file
(CMSC170_Lab3_8Puzzle_BFS.py).

This file is a test harness, not part of the submitted program. The merge is the step
that can break a working program, so this battery re-checks the finished file: that
every rule exists exactly once in it, that the search still gives the handout's
answer, that the game still plays, and that the GUI still runs on top of both.

Run it from the folder that holds CMSC170_Lab3_8Puzzle_BFS.py:

    python3 verify_merged.py

Every line prints PASS or FAIL. The script exits with status 1 if anything failed.
The GUI part needs a display, but the window stays withdrawn.
"""

import ast
import pathlib
import subprocess
import sys
import time

import tkinter as tk

import CMSC170_Lab3_8Puzzle_BFS as lab

SUBMISSION = pathlib.Path(__file__).with_name("CMSC170_Lab3_8Puzzle_BFS.py")
REPO = pathlib.Path(__file__).resolve().parent

GOAL = (1, 2, 3, 4, 5, 6, 7, 8, 0)
SAMPLE = (1, 5, 2, 7, 4, 3, 8, 6, 0)
DEEPEST = (8, 6, 7, 2, 5, 4, 3, 0, 1)
UNSOLVABLE = (1, 2, 3, 4, 5, 6, 8, 7, 0)
SOLUTION = list("AAWDWDXX")

results = []

def check(name, condition, detail=""):
    results.append((name, bool(condition)))
    print(f"  [{'PASS' if condition else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))
    return bool(condition)

def section(title):
    print(f"\n{title}")
    print("-" * len(title))


# 0. The file itself.

section("0. The submission file")

source = SUBMISSION.read_text()
tree = ast.parse(source)
names = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
for node in tree.body:
    if isinstance(node, ast.Assign):
        names += [t.id for t in node.targets if isinstance(t, ast.Name)]

for rule in ("get_possible_moves", "is_solvable", "is_valid_state", "validate_state",
             "MOVES", "Node", "bfs", "_inversions"):
    check(f"'{rule}' is defined once in the file", names.count(rule) == 1,
          f"found {names.count(rule)}")
check("the file does not import the members' files any more",
      "Task2_Lab3" not in source and "bfs_8puzzle" not in source)
check("the file is valid Python and compiles", bool(compile(source, str(SUBMISSION), "exec")))
check("the group's names are in the header",
      all(n in source for n in ("Senoy", "Royo", "Jomuad")))
check("the student number on the file is Jomuad's", "2023-00554" in source)
check("the file explains how to run it", "python3 CMSC170_Lab3_8Puzzle_BFS.py" in source)


# 1. The rules, once, and the same everywhere.

section("1. One set of rules")

check("the move generator takes the board the program uses", lab.get_possible_moves(SAMPLE) != {})
counts_ok = True
for blank_index in range(9):
    board = list(range(1, 9))
    board.insert(blank_index, 0)
    board = tuple(board)
    row, col = divmod(blank_index, 3)
    expected = 2 if (row, col) in ((0, 0), (0, 2), (2, 0), (2, 2)) else (3 if 0 in (row, col) or 2 in (row, col) else 4)
    if len(lab.get_possible_moves(board)) != expected:
        counts_ok = False
        print(f"         blank at {blank_index}: {len(lab.get_possible_moves(board))} moves, expected {expected}")
check("the blank has the right number of moves at all nine cells", counts_ok)
check("the game's validator accepts a legal key", lab.validate_move(SAMPLE, 'A'))
check("the game's validator refuses an illegal key", not lab.validate_move(SAMPLE, 'X'))
check("the game's validator refuses an unknown key", not lab.validate_move(SAMPLE, 'Z'))
check("the state validator accepts a good board", lab.is_valid_state(SAMPLE))
check("the state validator refuses a board with a repeated tile",
      not lab.is_valid_state((1, 2, 3, 4, 5, 6, 7, 8, 8)))
check("a typed board with a blank as ' ' is converted to 0",
      lab.to_state([1, 2, 3, 4, ' ', 8, 5, 6, 7]) == (1, 2, 3, 4, 0, 8, 5, 6, 7))
check("the game and the search call the same move generator",
      lab.game_moves(SAMPLE) == lab.get_possible_moves(SAMPLE))

check("the player's notation is kept: W means the blank moves up",
      lab.get_possible_moves((1, 2, 3, 4, 0, 5, 6, 7, 8))['W'] == (1, 0, 3, 4, 2, 5, 6, 7, 8))


# 2. Solvability and the search, as the handout states them.

section("2. BFS on the handout's boards")

check("the sample board is reported as solvable", lab.is_solvable(SAMPLE, GOAL))
check("a transposed tile is reported as unsolvable", not lab.is_solvable(UNSOLVABLE, GOAL))
check("the board on the handout's slide is unsolvable as printed",
      not lab.is_solvable((1, 2, 3, 0, 8, 6, 4, 7, 5), GOAL))

node, expanded = lab.bfs(SAMPLE, GOAL, verbose=False)
check("the sample board is solved in the handout's 8 moves", node is not None and node.depth == 8,
      f"{node.depth if node else None} moves")
check("it takes 149 expanded states, the number in the console output", expanded == 149,
      f"{expanded} expanded")
if node is None:
    check("the solution path is the handout's A A W D W D X X", False, "no path")
else:
    check("the solution path is the handout's A A W D W D X X",
          [step.action for step in node.path()[1:]] == SOLUTION)

start = time.perf_counter()
deep_node, deep_expanded = lab.bfs(DEEPEST, GOAL, verbose=False)
elapsed = time.perf_counter() - start
deep_depth = deep_node.depth if deep_node else None
check("the deepest 8-puzzle board is solved in 31 moves", deep_depth == 31, f"{deep_depth}")
check("it expands 181,349 of the 181,440 reachable states", deep_expanded == 181349,
      f"{deep_expanded} expanded")
check("it finishes in seconds", elapsed < 30, f"{elapsed:.2f} s")

already, already_expanded = lab.bfs(GOAL, GOAL, verbose=False)
check("an already solved board answers 0 moves", already.depth == 0 and already_expanded == 0)

check("the state space keeps the step cost of each connection",
      lab.expand(SAMPLE)[0][2] == lab.STEP_COST and len(lab.state_space) > 0)


# 3. The file input.

section("3. Reading a board from a file")

initial, goal = lab.parse_state_file(str(REPO / "sample_8_moves.txt"))
check("the sample file reads as the handout's two boards", initial == SAMPLE and goal == GOAL)
for name, why in (("invalid_duplicate.txt", "a repeated tile"),
                  ("invalid_format.txt", "a row with two values")):
    try:
        lab.parse_state_file(str(REPO / name))
        check(f"{name} is refused ({why})", False, "accepted")
    except ValueError:
        check(f"{name} is refused ({why})", True)
try:
    lab.parse_state_file(str(REPO / "not_here.txt"))
    check("a missing file raises OSError", False, "no error")
except OSError:
    check("a missing file raises OSError", True)

def run_menu(script_input, timeout=90):
    """Run the submission file with scripted answers to the menu."""
    return subprocess.run([sys.executable, SUBMISSION.name], cwd=REPO, input=script_input,
                          capture_output=True, text=True, timeout=timeout)

solved = run_menu("Q\n")
check("running the file asks how to run it and quits cleanly on Q",
      solved.returncode == 0 and "How do you want to run the program?" in solved.stdout
      and "with a GUI" in solved.stdout and "CLI only" in solved.stdout,
      f"exit {solved.returncode}")
after_choice = run_menu("2\nQ\n")
check("both tasks are offered once the way of running it is chosen",
      "play the 8-puzzle game (Task 2)" in after_choice.stdout
      and "solve a board with BFS (Task 3)" in after_choice.stdout,
      f"exit {after_choice.returncode}")
check("the menu ends cleanly when the input runs out",
      run_menu("1\n").returncode == 0 and "No input left" in run_menu("1\n").stdout)


# 4. The game.

section("4. The game")

check("the instructions print before anything is asked for",
      "8-Puzzle Game Start" in subprocess.run([sys.executable, "-c",
          "import CMSC170_Lab3_8Puzzle_BFS as m; m.show_instructions()"], cwd=REPO,
          capture_output=True, text=True).stdout)

played = run_menu("2\n1\n[1,5,2,7,4,3,8,6,' ']\n\n" + "".join(k + "\n" for k in SOLUTION))
last_line = played.stdout.strip().splitlines()[-1] if played.stdout.strip() else "(no output)"
check("CLI + the game plays through to the solved board",
      "Solved in 8 moves!" in played.stdout, last_line)
check("the CLI game refuses an unsolvable pair",
      "parity mismatch" in run_menu("2\n1\n[1,2,3,4,5,6,8,7,' ']\n[1,2,3,4,5,6,7,8,' ']\n").stdout)
check("the CLI game ends cleanly when the input runs out",
      "No input left" in run_menu("2\n1\n[1,5,2,7,4,3,8,6,' ']\n\nA\n").stdout)

# Task 3 in the CLI: the file option, straight from the menu.
bfs_run = run_menu("2\n2\nsample_8_moves.txt\n")
check("CLI + BFS reads the file and finds the handout's 8 moves",
      "Total number of moves to reach the goal state = 8" in bfs_run.stdout
      and "Nodes expanded: 149" in bfs_run.stdout)
check("the BFS path explains the algorithm before searching",
      "=== Breadth-First Search (BFS) ===" in bfs_run.stdout
      and bfs_run.stdout.index("Breadth-First Search (BFS)") < bfs_run.stdout.index("Searching..."))
check("CLI + BFS reports an unsolvable file",
      "UNSOLVABLE" in run_menu("2\n2\nunsolvable_swap.txt\n").stdout)
check("CLI + BFS refuses a bad file with a message",
      "Could not read input" in run_menu("2\n2\ninvalid_duplicate.txt\n").stdout)


# 5. The GUI, on top of both parts.

section("5. The GUI")

root = tk.Tk()
root.withdraw()
app = lab.PuzzleGUI(root)
check("the window builds on the merged code", app.board == lab.DEFAULT_INITIAL)
check("the optimal-solution button is off before the puzzle is solved",
      str(app.solve_button["state"]) == "disabled")

app.new_game(SAMPLE, GOAL)
for key in SOLUTION:
    app.play(key)
check("the puzzle can be solved in the window", app.board == GOAL and app.solved)
check("the button wakes up once the puzzle is solved",
      str(app.solve_button["state"]) == "normal")
check("the window offers BFS's 8 moves", app.optimal_moves == SOLUTION)
check("the window says which count is optimal", "optimal 8" in app.status["text"])

lab.STEP_MS = 1
app.show_optimal()
check("the replay restarts from the board the player began with", app.board == SAMPLE)
pumps = 0
while app.replay_job is not None and pumps < 40:
    root.after(15, root.quit)
    root.mainloop()
    pumps += 1
recorded = [step.state for step in app.optimal.path()[1:]] if app.optimal else None
check("the replay shows exactly the boards BFS recorded", app.replay_boards == recorded,
      f"{len(app.replay_boards)} steps")
check("the replay ends on the goal", app.board == GOAL)

app.new_game(UNSOLVABLE, GOAL)
check("the window refuses an impossible board", app.in_play is False)
root.destroy()

# the window in BFS mode, and the GUI's version of the Task 3 file option
bfs_root = tk.Tk()
bfs_root.withdraw()
bfs_app = lab.PuzzleGUI(bfs_root, mode="bfs")
check("the window opens in BFS mode with the button ready",
      bfs_app.mode == "bfs" and str(bfs_app.solve_button["state"]) == "normal")
check("BFS mode says what to press", "BFS mode" in bfs_app.status["text"])
check("the answer can be asked for without solving the puzzle", bfs_app.show_optimal())
check("BFS mode records the working out",
      bfs_app.optimal_expanded == 149 and bfs_app.optimal_moves == SOLUTION,
      f"{bfs_app.optimal_expanded} states expanded")
bfs_app.stop_replay()
check("a board file can be loaded in the window",
      bfs_app.load_from_file(str(REPO / "sample_8_moves.txt")))
check("the loaded boards are the file's boards",
      bfs_app.initial == SAMPLE and bfs_app.goal == GOAL)
check("a bad file is refused in the window",
      bfs_app.load_from_file(str(REPO / "invalid_format.txt")) is False)
bfs_root.destroy()

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
