"""
DS 170 / CMSC 170 - Laboratory Exercise No. 3
Member 3 - edge-case check battery for the 8-puzzle BFS program.

This file is a test harness, not part of the program itself. It imports
bfs_8puzzle.py and checks the cases the group listed in the division of work:
unsolvable boards, an already solved start, invalid input files, and the blank
on every boundary of the 3x3 board. It also replays the solution path to check
the moves are real moves, and compares BFS's answer against a slower search to
confirm the solution is the shortest one.

Run it from the folder that holds bfs_8puzzle.py:

    python test_edge_cases.py

Every line prints PASS or FAIL. The script exits with status 1 if anything
failed, so it can be used as the last check before submission.
"""

import sys
import time
from collections import deque

import bfs_8puzzle as puzzle


# Tiny check counter. I wanted the output to be readable in a screenshot, so
# each check prints one line and the summary at the end prints the totals.

results = []

def check(name, condition, detail=""):
    results.append((name, bool(condition)))
    print(f"  [{'PASS' if condition else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))
    return bool(condition)

def section(title):
    print(f"\n{title}")
    print("-" * len(title))


# Boards used by the checks below.

GOAL = (1, 2, 3, 4, 5, 6, 7, 8, 0)

# The sample board from the handout. Reaches the goal in 8 moves.
SAMPLE = (1, 5, 2, 7, 4, 3, 8, 6, 0)

# Solvable, but 31 moves away from the goal. This is the deepest 8-puzzle
# instance, so BFS has to work through the whole reachable state space.
DEEPEST = (8, 6, 7, 2, 5, 4, 3, 0, 1)

# One transposition away from the goal, so it can never reach it.
UNSOLVABLE = (1, 2, 3, 4, 5, 6, 8, 7, 0)

# Goal State B from the handout: a different, equally valid goal.
GOAL_B = (1, 2, 3, 8, 0, 4, 7, 6, 5)


# 1. Blank on the boundary of the board.
# The move generator must produce only moves that stay inside the 3x3 board.
# A blank in the middle has four moves, an edge has three, a corner has two.

section("1. Boundary moves of the blank")

def blank_at(index):
    """Put the blank at `index` and fill the rest of the board in order."""
    rest = [t for t in range(1, 9)]
    board = []
    for position in range(9):
        board.append(0 if position == index else rest.pop(0))
    return tuple(board)

EXPECTED_COUNTS = {
    0: 2,  # top left corner: right and down
    1: 3,  # top edge
    2: 2,  # top right corner
    3: 3,  # left edge
    4: 4,  # center
    5: 3,  # right edge
    6: 2,  # bottom left corner
    7: 3,  # bottom edge
    8: 2,  # bottom right corner
}

for index, expected in EXPECTED_COUNTS.items():
    state = blank_at(index)
    moves = puzzle.get_possible_moves(state)
    row, col = divmod(index, 3)
    where = f"blank at row {row}, col {col} (index {index})"
    check(f"{where}: {expected} legal moves", len(moves) == expected,
          f"got {len(moves)}")

# Every successor has to be the same board with exactly the blank and one
# neighbouring tile exchanged. This is the rule the handout stresses: one
# board changes at a time.
bad_swaps = []
for index in range(9):
    state = blank_at(index)
    for action, next_state in puzzle.get_possible_moves(state):
        differing = [p for p in range(9) if state[p] != next_state[p]]
        if len(differing) != 2 or 0 not in [state[p] for p in differing]:
            bad_swaps.append((index, action, next_state))
check("every move swaps the blank with exactly one tile",
      not bad_swaps, f"{len(bad_swaps)} bad successors")

check("a move never produces a board outside 3x3",
      all(len(next_state) == 9 for index in range(9)
          for _, next_state in puzzle.get_possible_moves(blank_at(index))))

# The tile that moved must be orthogonally next to the blank, and the tile
# numbers themselves must be the same set as before (nothing invented).
def orthogonal_swap_ok(state, next_state):
    blank = state.index(0)
    moved = next_state.index(0)
    same_row = blank // 3 == moved // 3 and abs(blank - moved) == 1
    same_col = blank % 3 == moved % 3 and abs(blank - moved) == 3
    return (same_row or same_col) and sorted(state) == sorted(next_state)

check("the moved tile is orthogonally adjacent to the blank",
      all(orthogonal_swap_ok(blank_at(i), s)
          for i in range(9) for _, s in puzzle.get_possible_moves(blank_at(i))))


# 2. The sample board from the handout: 8 moves.
# The handout prints "Total number of moves to reach the goal state = 8", so
# this is also the check that the search agrees with the handout.

section("2. Sample board from the handout")

goal_node, expanded = puzzle.bfs(SAMPLE, GOAL, verbose=False)
check("the sample board is reported as solvable", puzzle.is_solvable(SAMPLE, GOAL))
check("a solution was found", goal_node is not None)
check("total number of moves is 8", goal_node is not None and goal_node.depth == 8,
      f"got {goal_node.depth if goal_node else 'No solution'}")
check("the goal node's state is the goal state",
      goal_node is not None and goal_node.state == GOAL)

# Replaying the move sequence is the strongest check I have that the search
# and the move generator talk about the same board. Each action is re-applied
# to the initial state and has to be one of the legal moves at that point.
def replay(initial, node):
    """Walk the solution path and re-apply each move to the initial state.

    Returns (steps, state, error). `error` is None when every action was a
    legal move and the recorded board matched the board I got by playing it.
    """
    state = initial
    for step, path_node in enumerate(node.path()[1:], start=1):
        legal = dict(puzzle.get_possible_moves(state))
        if path_node.action not in legal:
            return step, state, f"'{path_node.action}' is not legal here"
        state = legal[path_node.action]
        if state != path_node.state:
            return step, state, f"board after step {step} is not the recorded board"
    return len(node.path()) - 1, state, None

steps, final_state, replay_error = replay(SAMPLE, goal_node) if goal_node else (0, None, "no path")
check("every move in the sequence is legal where it is played",
      replay_error is None, replay_error or "")
check("replaying the whole sequence lands on the goal state",
      final_state == GOAL, str(final_state))
check("the number of moves equals the depth of the goal node",
      goal_node is not None and steps == goal_node.depth, f"{steps} moves")

# BFS should not need to expand the entire state space for this board.
check("the sample board is solved without expanding everything",
      expanded < 181440, f"{expanded} states expanded")


# 3. An already solved start.
# The start equals the goal, so the answer is the initial state itself and
# zero moves. Running the search here must not crash or loop.

section("3. Already solved start")

goal_node, expanded = puzzle.bfs(GOAL, GOAL, verbose=False)
check("an already solved board returns a goal node", goal_node is not None)
check("it reports 0 moves", goal_node is not None and goal_node.depth == 0,
      f"got {goal_node.depth if goal_node else 'None'}")
check("the recorded state is the start board itself",
      goal_node is not None and goal_node.state == GOAL)
check("nothing is expanded when the start is already the goal", expanded == 0,
      f"{expanded} expanded")
check("the path has one node and no moves",
      goal_node is not None and len(goal_node.path()) == 1
      and goal_node.path()[0].action is None)

# The same start with a different goal has to be searched normally. This goal
# is the identity board with the blank moved into the middle. Like the identity
# it has an even number of inversions, so it is in the same reachable half of
# the state space.
GOAL_CENTER = (1, 2, 3, 4, 0, 5, 6, 7, 8)

goal_node_b, _ = puzzle.bfs(GOAL, GOAL_CENTER, verbose=False)
check("the same start is searched normally for a different goal",
      goal_node_b is not None and goal_node_b.state == GOAL_CENTER,
      f"{goal_node_b.depth if goal_node_b else 'None'} moves")

# Goal State B from the handout: 1,2,3 / 8,_,4 / 7,6,5. Counting inversions
# gives 7 against the identity's 0, so it sits in the other half of the state
# space and is not reachable from Goal State A. BFS has to say so instead of
# exploring the space and failing.
check("Goal State B is unreachable from Goal State A (different parity)",
      not puzzle.is_solvable(GOAL, GOAL_B))
check("so BFS returns no path for it",
      puzzle.bfs(GOAL, GOAL_B, verbose=False)[0] is None)


# 4. Unsolvable boards.
# Half of the 9! boards cannot reach the goal. BFS would otherwise walk the
# whole state space and then give up, so the inversion parity check has to
# catch these two boards up front.

section("4. Unsolvable boards")

check("the swapped pair board is rejected as unsolvable",
      not puzzle.is_solvable((1, 2, 3, 4, 5, 6, 8, 7, 0), GOAL))
check("the board from the handout's slide is rejected as unsolvable",
      not puzzle.is_solvable((1, 2, 3, 0, 8, 6, 4, 7, 5), GOAL))
check("the sample board is still accepted as solvable",
      puzzle.is_solvable(SAMPLE, GOAL))
check("the deepest board is accepted as solvable",
      puzzle.is_solvable(DEEPEST, GOAL))

# solve() has to stop with a message instead of exploring 181,440 states.
start = time.perf_counter()
unsolvable_result = puzzle.solve((1, 2, 3, 4, 5, 6, 8, 7, 0), GOAL)
elapsed = time.perf_counter() - start
check("solve() returns None for an unsolvable board", unsolvable_result is None)
check("solve() answers the unsolvable board immediately",
      elapsed < 0.5, f"{elapsed:.3f} s")

# The parity check has to look at the goal too, not only at the start.
check("two different goals from the same start are not both reachable",
      puzzle.is_solvable(SAMPLE, GOAL) != puzzle.is_solvable(SAMPLE, (1, 2, 3, 4, 5, 6, 8, 7, 0)))


# 5. Invalid input.
# The parser has to reject a board that is not a permutation of 0-8, and it
# has to reject a row with the wrong number of values, without a traceback.

section("5. Invalid input files")

def expect_value_error(path, what):
    try:
        puzzle.parse_state_file(path)
    except ValueError as error:
        check(f"{path} is rejected: {what}", True, str(error)[:70])
        return
    except OSError as error:
        check(f"{path} is rejected: {what}", False, f"OSError: {error}")
        return
    check(f"{path} is rejected: {what}", False, "no error raised")

expect_value_error("invalid_duplicate.txt", "a repeated tile")
expect_value_error("invalid_format.txt", "a row with two values")

# A file that is not there at all should raise OSError, which __main__ catches.
try:
    puzzle.parse_state_file("no_such_file_here.txt")
    check("a missing file raises OSError", False, "no error raised")
except OSError:
    check("a missing file raises OSError", True)
except ValueError as error:
    check("a missing file raises OSError", False, f"ValueError instead: {error}")

# Direct checks on the validator, for boards a file can't easily express.
for vector, why in [
    ((1, 2, 3, 4, 5, 6, 7, 8, 8), "duplicated 8"),
    ((1, 2, 3, 4, 5, 6, 7, 8), "only 8 tiles"),
    ((1, 2, 3, 4, 5, 6, 7, 8, 9), "9 is not a tile"),
    ((0, 0, 1, 2, 3, 4, 5, 6, 7), "two blanks"),
]:
    try:
        puzzle.validate_state(vector)
        check(f"validate_state rejects {why}", False, "accepted")
    except ValueError:
        check(f"validate_state rejects {why}", True)

# And it has to accept the good boards, otherwise the checks above prove nothing.
try:
    puzzle.validate_state(GOAL)
    puzzle.validate_state(SAMPLE)
    check("validate_state accepts both good boards", True)
except ValueError as error:
    check("validate_state accepts both good boards", False, str(error))

# The valid sample file has to parse to the boards I expect.
initial, goal = puzzle.parse_state_file("sample_8_moves.txt")
check("sample_8_moves.txt parses to the right initial state", initial == SAMPLE)
check("sample_8_moves.txt parses to the right goal state", goal == GOAL)
check("the blank is read as 0, not left as a character",
      all(isinstance(v, int) for v in initial) and 0 in initial)


# 6. Is the BFS path really the shortest one?
# BFS claims optimality, so I check it against a second search instead of
# trusting the printout. Two checks: a queue search that tests the goal when
# the node is taken out of the queue (a different place than bfs_8puzzle.py),
# and an iterative deepening search that fails to find anything one level
# shallower.

section("6. Shortest path check")

def bfs_goal_on_pop(initial, goal):
    """Independent BFS: the goal test happens when a node leaves the queue."""
    frontier = deque([(initial, 0)])
    seen = {initial}
    while frontier:
        state, depth = frontier.popleft()
        if state == goal:
            return depth
        for _, next_state in puzzle.get_possible_moves(state):
            if next_state not in seen:
                seen.add(next_state)
                frontier.append((next_state, depth + 1))
    return None

def depth_limited(initial, goal, limit):
    """Depth-limited DFS. Returns True if the goal is reachable within limit."""
    stack = [(initial, 0)]
    seen = {initial: 0}
    while stack:
        state, depth = stack.pop()
        if state == goal:
            return True
        if depth == limit:
            continue
        for _, next_state in puzzle.get_possible_moves(state):
            if seen.get(next_state, 99) > depth + 1:
                seen[next_state] = depth + 1
                stack.append((next_state, depth + 1))
    return False

for label, board, expected_depth in [("sample board", SAMPLE, 8),
                                     ("deepest board", DEEPEST, 31)]:
    node, _ = puzzle.bfs(board, GOAL, verbose=False)
    depth = node.depth if node else None
    check(f"{label}: BFS depth is {expected_depth}", depth == expected_depth, f"got {depth}")
    check(f"{label}: a queue search with the goal test on pop agrees",
          depth is not None and bfs_goal_on_pop(board, GOAL) == depth,
          f"got {bfs_goal_on_pop(board, GOAL)}")
    if depth is not None and depth <= 8:
        check(f"{label}: no solution exists in {depth - 1} moves",
              not depth_limited(board, GOAL, depth - 1))


# 7. The deepest 8-puzzle instance.
# 31 moves is the longest possible shortest path on a 3x3 board, so this run
# touches the whole reachable state space. If BFS is going to run out of
# memory or take minutes, it happens here.

section("7. Deepest board (31 moves)")

start = time.perf_counter()
deep_node, deep_expanded = puzzle.bfs(DEEPEST, GOAL, verbose=False)
deep_elapsed = time.perf_counter() - start
check("the deepest board is solved", deep_node is not None)
check("it takes 31 moves", deep_node is not None and deep_node.depth == 31,
      f"got {deep_node.depth if deep_node else 'None'}")
check("it finishes in a few seconds", deep_elapsed < 30, f"{deep_elapsed:.2f} s")
print(f"        31-move board: {deep_expanded} states expanded in {deep_elapsed:.2f} s")

# The whole reachable half of the state space, counted by walking it without
# stopping early. 9! is 362,880 boards, but only half of them can be reached
# from a given start, which is the number the report quotes.
def count_reachable(initial):
    seen = {initial}
    frontier = deque([initial])
    while frontier:
        state = frontier.popleft()
        for _, next_state in puzzle.get_possible_moves(state):
            if next_state not in seen:
                seen.add(next_state)
                frontier.append(next_state)
    return len(seen)

reachable = count_reachable(DEEPEST)
check("the reachable half of the state space is 181,440 states",
      reachable == 181440, f"{reachable} states")
check("BFS stops before expanding all of them", deep_expanded < reachable,
      f"{deep_expanded} expanded out of {reachable}")


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
