"""
DS 170 / CMSC 170 - Laboratory Exercise No. 3
Member 3 - check battery for the Task 2 game, plus the checks that the game and
the search really use one set of rules.

This file is a test harness, not part of the program. It imports Task2_Lab3.py
and also runs the game as a separate process so the input prompts and the printed
messages are tested the way a player meets them.

Run it from the folder that holds Task2_Lab3.py:

    python test_task2_game.py

Every line prints PASS or FAIL. The script exits with status 1 if anything failed.
"""

import pathlib
import subprocess
import sys

import Task2_Lab3 as game

REPO = pathlib.Path(__file__).resolve().parent
results = []

def check(name, condition, detail=""):
    results.append((name, bool(condition)))
    print(f"  [{'PASS' if condition else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))
    return bool(condition)

def section(title):
    print(f"\n{title}")
    print("-" * len(title))


def board_with_blank_at(index, blank=game.BLANK):
    """A board with the blank at `index` and the tiles in order everywhere else."""
    rest = list(range(1, 9))
    return tuple(blank if position == index else rest.pop(0) for position in range(9))


# 1. Boundary moves of the blank.
# Same rule as the search: a corner has two moves, an edge three, the centre four.

section("1. Boundary moves in the game")

EXPECTED = {0: 2, 1: 3, 2: 2, 3: 3, 4: 4, 5: 3, 6: 2, 7: 3, 8: 2}
for index, expected in EXPECTED.items():
    moves = game.get_possible_moves(board_with_blank_at(index))
    row, col = divmod(index, 3)
    check(f"blank at row {row}, col {col}: {expected} legal moves",
          len(moves) == expected, f"got {len(moves)}")

# The blank has to stay on the board and the move has to swap it with one tile.
bad = []
for index in range(9):
    state = board_with_blank_at(index)
    for key, next_state in game.get_possible_moves(state).items():
        differing = [p for p in range(9) if state[p] != next_state[p]]
        if len(differing) != 2 or game.BLANK not in [state[p] for p in differing]:
            bad.append((index, key, next_state))
check("every move swaps the blank with exactly one tile", not bad,
      f"{len(bad)} bad successors")
check("every move produces a board that is still 9 cells",
      all(len(s) == 9 for index in range(9)
          for s in game.get_possible_moves(board_with_blank_at(index)).values()))

# The state is a tuple, so a move cannot change the board it came from.
before = board_with_blank_at(8)
moved = game.get_possible_moves(before)['W']
check("the new state is a tuple, not a list", isinstance(moved, tuple))
check("the board the move came from is unchanged", before == board_with_blank_at(8))
check("the move really did change the board", moved != before)


# 2. validate_move.
# The validator has to say yes to the legal keys and no to everything else.

section("2. validate_move")

state = (1, 5, 2, 7, 4, 3, 8, 6, game.BLANK)      # blank in the bottom-right corner
legal = game.get_possible_moves(state)
check("both legal keys are accepted", all(game.validate_move(state, k) for k in legal),
      f"legal keys: {sorted(legal)}")
check("the corner board really only allows 'A' and 'W'", sorted(legal) == ['A', 'W'],
      f"got {sorted(legal)}")
check("keys that would leave the board are refused",
      not game.validate_move(state, 'X') and not game.validate_move(state, 'D'))
for key, why in [('Z', "unknown key"), ('', "empty key"), ('DD', "two keys at once"),
                 ('w', "lowercase key"), (None, "no key at all")]:
    check(f"validate_move refuses {why}", not game.validate_move(state, key))
check("the game offers only the keys it accepts",
      all(k in game.MOVES for k in legal))


# 3. Reading what the player types.
# The lab sheet's format has a blank typed as ' ', and the state inside the program
# has the blank as 0. to_state() is the one place that conversion happens.

section("3. Typed input is converted to the state form")

converted = game.to_state([1, 2, 3, 4, ' ', 8, 5, 6, 7])
check("the lab sheet format converts to the internal state",
      converted == (1, 2, 3, 4, 0, 8, 5, 6, 7), str(converted))
check("a blank typed as 0 also converts", game.to_state([1, 2, 3, 4, 0, 8, 5, 6, 7]) == converted)
check("a blank typed as '_' also converts", game.to_state([1, 2, 3, 4, '_', 8, 5, 6, 7]) == converted)
check("the converted state is a tuple", isinstance(converted, tuple))

for items, why in [([1, 2, 3, 4, ' ', 8, 5, 6, 8], "a repeated tile"),
                   ([1, 2, 3, 4, ' ', 8, 5, 6], "only 8 items"),
                   ([1, 2, 3, 4, ' ', 8, 5, 6, 7, 0], "10 items"),
                   ([1, 2, 3, 4, ' ', 8, 5, 6, '7'], "a tile written as a string"),
                   ([1, 2, 3, 4, ' ', ' ', 5, 6, 7], "two blanks"),
                   ([1, 2, 3, 4, ' ', 8, 5, 6, 9], "a tile numbered 9")]:
    try:
        game.to_state(items)
        check(f"to_state refuses {why}", False, "accepted")
    except ValueError:
        check(f"to_state refuses {why}", True)

check("is_valid_state accepts the internal form", game.is_valid_state(converted))
check("is_valid_state refuses a board with the blank still as ' '",
      not game.is_valid_state([1, 2, 3, 4, ' ', 8, 5, 6, 7]))
check("is_valid_state refuses True/False in place of a tile",
      not game.is_valid_state((1, 2, 3, 4, 5, 6, 7, 8, True)))


# 4. Solvability of the game's own example board.
# The board printed in the lab sheet's input-format example, once converted, cannot
# reach the goal state: 1,2,3 / 4,_,8 / 5,6,7 has an odd number of inversions.
# The game has to say so instead of letting the player try forever.

section("4. Solvability")

check("the goal board is solvable from itself", game.is_solvable(game.DEFAULT_GOAL, game.DEFAULT_GOAL))
check("the lab sheet's example board is not solvable to the goal",
      not game.is_solvable(game.to_state([1, 2, 3, 4, ' ', 8, 5, 6, 7]), game.DEFAULT_GOAL))
check("the 8-move board is solvable",
      game.is_solvable((1, 5, 2, 7, 4, 3, 8, 6, 0), game.DEFAULT_GOAL))
check("one transposed tile makes a board unsolvable",
      not game.is_solvable((1, 2, 3, 4, 5, 6, 8, 7, 0), game.DEFAULT_GOAL))


# 5. The game as a player meets it.
# Each run feeds the prompts line by line: the initial state, the goal, then the moves.

section("5. Playing the game end to end")

def play(script_input, label, timeout=60):
    """Run the game with this input. Returns (status, output, error)."""
    run = subprocess.run([sys.executable, "Task2_Lab3.py"], cwd=REPO,
                         input=script_input, capture_output=True, text=True, timeout=timeout)
    return run.returncode, run.stdout, run.stderr

MOVES_TO_SOLVE = "A\nA\nW\nD\nW\nD\nX\nX\n"

status, out, err = play("[1,5,2,7,4,3,8,6,' ']\n\n" + MOVES_TO_SOLVE, "solve the 8-move board")
check("the program explains the problem and the rules before asking for input",
      "8-Puzzle Game Start" in out and "Rules:" in out
      and out.index("Rules:") < out.index("Initial state:"))
check("the instructions show the lab sheet's input format",
      "[1, 2, 3, 4, ' ', 8, 5, 6, 7]" in out)
check("the key legend is printed", "'W' Move Up" in out and "'D' Move Right" in out)
check("the board the player typed is shown with the blank as a gap", "| 6 |   |" in out)
check("playing the eight moves solves the board", "Solved in 8 moves!" in out)
# The board printed just before the final message has to be the goal board.
final_block = out.split("Solved in 8 moves!")[0].rstrip().splitlines()[-7:]
check("the last board printed is the goal board",
      final_block[:7] == ["+---+---+---+", "| 1 | 2 | 3 |", "+---+---+---+",
                          "| 4 | 5 | 6 |", "+---+---+---+", "| 7 | 8 |   |",
                          "+---+---+---+"], " | ".join(final_block))
check("the run exits normally", status == 0 and err.strip() == "", f"status {status}")

status, out, err = play("[1,5,2,7,4,3,8,6,' ']\n\nZ\n" + MOVES_TO_SOLVE, "invalid key first")
check("an invalid key is refused with a message", "Invalid move!" in out)
check("the game continues after an invalid key", "Solved in 8 moves!" in out)

status, out, err = play("[1,5,2,7,4,3,8,6,' ']\n\nQ\n", "quit with Q")
check("Q ends the game at the move prompt", "Game ended." in out)

status, out, err = play("[1,2,3,4,5,6,8,7,' ']\n[1,2,3,4,5,6,7,8,' ']\n", "unsolvable pair")
check("an unsolvable pair is refused before play starts",
      "parity mismatch" in out and "Moves so far" not in out)

status, out, err = play("[1,2,3,4,5,6,7,8,' ']\n\n", "already solved start")
check("an already solved start reports zero moves", "Solved in 0 moves!" in out)

status, out, err = play("[1,2,3,4,8,5,6,7]\nnot a list\n[1,2,3,4,' ',8,5,6,7]\nQ\n",
                        "bad inputs then quit")
check("a wrong number of cells is refused and re-prompted", "Could not read that" in out)
check("a junk line is refused and re-prompted", out.count("Could not read that") >= 2,
      f"{out.count('Could not read that')} refusals")
check("Q at the state prompt ends the game without a crash",
      status == 0 and "Traceback" not in err and "Game ended." in out)

status, out, err = play("", "no input at all")
check("running out of input ends cleanly instead of crashing",
      status == 0 and "Traceback" not in err, f"status {status}")


# 6. One set of rules for the game and the search.
# This is the point of the shared code: the moves the player is offered and the
# moves the search takes have to be the same moves.

section("6. The game and the search agree")

import bfs_8puzzle as search

same_board = (1, 5, 2, 7, 4, 3, 8, 6, 0)
check("the search uses the game's move generator, not a copy",
      search.get_possible_moves is game.get_possible_moves)
check("the game's move set is the search's move set",
      sorted(game.get_possible_moves(same_board)) == sorted(search.get_possible_moves(same_board)))
check("both produce the same successor boards",
      game.get_possible_moves(same_board) == search.get_possible_moves(same_board))

# A board typed into the game, put through the search.
typed = game.to_state([1, 5, 2, 7, 4, 3, 8, 6, ' '])
goal_node, _ = search.bfs(typed, game.DEFAULT_GOAL, verbose=False)
check("a board typed into the game can be solved by the search",
      goal_node is not None and goal_node.depth == 8)

if goal_node is not None:
    check("the search's move sequence is legal for the game's validator",
          all(game.validate_move(node.parent.state, node.action)
              for node in goal_node.path()[1:]))

    # And the other direction: a board the search expanded can be played in the game.
    some_state = goal_node.path()[3].state
    check("a state from the search path is a valid game state", game.is_valid_state(some_state))
    check("the game offers moves for a state the search produced",
          len(game.get_possible_moves(some_state)) >= 2)


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
