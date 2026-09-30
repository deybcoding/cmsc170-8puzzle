"""
DS 170 / CMSC 170 - Laboratory Exercise No. 3
Task 3: Breadth-First Search on the 8-Puzzle 
"""

from collections import deque
import sys

# The move rules and the parity check live in the Task 2 game file. The search
# imports them instead of writing them a second time, so the game and the search
# always agree about what a legal move is.
from Task2_Lab3 import get_possible_moves, is_valid_state, is_solvable


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

# The move generator is Task 2's get_possible_moves(state), imported above. It
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

# is_solvable(initial, goal) is Task 2's parity check, imported above. It lets the
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

if __name__ == "__main__":
    describe_bfs()
    path = sys.argv[1] if len(sys.argv) > 1 else input("Path to input file (e.g. sample_input.txt): ").strip()
    try:
        initial_state, goal_state = parse_state_file(path)
    except (OSError, ValueError) as e:
        sys.exit(f"Could not read input: {e}")
    print("Initial state:\n" + board_str(initial_state))
    print("Goal state:\n" + board_str(goal_state))
    print("\nSearching...")
    solve(initial_state, goal_state)
