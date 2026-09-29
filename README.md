# CMSC 170 – Laboratory Exercise 3: 8-Puzzle BFS Solver

## Member 2 Contribution — BFS Implementation & File I/O (Task 3)

---

## Overview

This module implements **Breadth-First Search (BFS)** to solve the 8-puzzle problem.  
It contains the `Node` class, the `bfs()` function, a file-input parser, and formatted output.

---

## Files

| File | Description |
|------|-------------|
| `bfs_8puzzle.py` | Main BFS solver (Member 2's Task 3 implementation) |
| `sample_input.txt` | Sample input file with initial and goal state |
| `invalid_format.txt` | Test file for invalid input handling |

---

## How to Run

```bash
python bfs_8puzzle.py sample_input.txt
```

Or run without arguments to be prompted for a file path:

```bash
python bfs_8puzzle.py
```

---

## Input File Format

The input file must contain **two 3×3 blocks** of comma-separated numbers, with `0` representing the blank tile.

```
1,2,3
6,0,8
4,7,5

1,2,3
4,5,6
7,8,0
```

- First block → **Initial state**
- Second block → **Goal state**
- Blank lines between blocks are allowed

---

## Sample Output

```
Root Node (Level 0)
  1 2 3
  6   8
  4 7 5

Level 1  (blank moved Left, 'A')
  1 2 3
    6 8
  4 7 5
...
Total number of moves to reach the goal state = 8
```

---

## Member 2 Implementation Details

### `Node` class
Stores each search-tree node with:
- `state` – tuple of 9 integers (0 = blank)
- `parent` – pointer to parent `Node`
- `action` – move that produced this node (`W/A/X/D`)
- `depth` – level in the search tree
- `path_cost` – g(n), cost from root (each move = 1)
- `path()` – reconstructs the solution path from root to this node

### `bfs(initial_state, goal_state)`
- Uses a **FIFO deque** as the frontier
- Tracks visited states in a **set** to avoid revisiting
- Goal test is performed **when a node is generated** (optimal for BFS)
- Returns `(goal_node, nodes_expanded)`

### `parse_state_file(path)`
- Reads two 3×3 blocks from a `.txt` file
- Validates that each state contains digits 0–8 exactly once
- Raises `ValueError` on malformed input

### Output
- Prints each board state level-by-level
- Reports total move count and the full move sequence
