# 2. Sudoku Solver — BFS with Backtracking

> Write a program that solves a Sudoku. The program has to handle three levels: **Easy, Medium, Hard**.

Files:

| File | Content |
|---|---|
| `sudoku_bfs.py` | BFS with backtracking, objective function, landscape, CLI |
| `puzzles.py` | puzzle bank (2 puzzles per level), difficulty rater, random puzzle generator |

---

## 2.1 Modeling

A 9 × 9 grid is divided into 9 rows, 9 columns and 9 boxes of 3 × 3 (27 *units*). Some cells are given (*clues*).

| Element | Definition |
|---|---|
| **Given** | the clues — fixed digits in some cells |
| **Decision** | a digit for every empty cell |
| **Hard constraints** | every row, every column and every 3×3 box contains each digit 1..9 exactly once; clues cannot be changed |
| **Soft constraints** | none — pure satisfaction problem (a proper Sudoku has exactly one solution) |

### Three levels

The program rates every puzzle with the human solving techniques it needs (`puzzles.rate`):

| Level | Definition | Puzzles in the bank |
|---|---|---|
| **Easy** | solvable with *naked singles* only (a cell with exactly one possible digit) | Wikipedia example (30 clues), Project Euler 96 grid 01 (32 clues) |
| **Medium** | also needs *hidden singles* (a digit that fits in only one cell of a unit) | two generated puzzles (25 and 26 clues) |
| **Hard** | singles are not enough — guessing / search is necessary | *AI Escargot* (23 clues) and *Everest* (21 clues) by Arto Inkala |

New puzzles of any level can be generated with `--generate easy|medium|hard` (a random full grid is created, clues are removed while the solution stays unique, and the result is re-rated).

## 2.2 Representation

**Solution representation** — a string of 81 characters, row by row (`.` = empty):

```
53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79
```

| | |
|---|---|
| **Variables** | x(r, c) for every **empty** cell (r, c) — e = 81 − clues variables |
| **Domain** | D(x) = {1, …, 9} (reduced to the digits not used by the cell's 20 *peers*) |
| **Constraints** | all-different(row r), all-different(column c), all-different(box b) for all r, c, b; x(r,c) = clue for given cells |

**Problem representation (search state)** — a partially filled grid.

* **Initial state:** the puzzle.
* **Action:** write a digit into one empty cell.
* **Successor:** the same grid with one more filled cell.
* **Goal test:** no empty cell left (all constraints are checked on the way).
* **Depth of every goal** = e (the number of empty cells).

## 2.3 Objective function

```
f(G) = Σ_{u ∈ 27 units} ( 9 − |distinct digits in u| )   +   |changed clues|
```

For a complete grid, `9 − |distinct digits|` is the number of duplicated digits in the unit, so

`f(G) = 0  ⇔  every row, column and box contains 1..9  ⇔  G is a solution.`

The search never generates a node with a duplicate (backtracking), so for every node the "duplicate part" of f is 0 and only empty cells remain; the goal is the node with f = 0. The function `objective()` evaluates any grid; every printed solution has f = 0.

## 2.4 Landscape (size of the search space)

Full grid: 9^81 = **1.97 · 10^77** candidate grids, of which only **6.67 · 10^21** are valid Sudoku grids.

For each puzzle (`python sudoku_bfs.py --landscape`):

| Puzzle | Empty e | A: 9^e | B: rows as permutations Π(missing_r)! | C: Π \|D(cell)\| after clues | random grids of B: mean f |
|---|---|---|---|---|---|
| easy-1 | 51 | 4.64·10^48 | 2.41·10^23 | 4.26·10^22 | 46.7 |
| easy-2 | 49 | 5.73·10^46 | 7.80·10^21 | 1.52·10^23 | 43.5 |
| medium-1 | 56 | 2.74·10^53 | 2.97·10^27 | 4.44·10^31 | 48.7 |
| medium-2 | 55 | 3.04·10^52 | 9.25·10^26 | 6.47·10^31 | 47.7 |
| hard-1 (Escargot) | 58 | 2.22·10^55 | 1.25·10^29 | 1.15·10^33 | 50.8 |
| hard-2 (Everest) | 60 | 1.80·10^57 | 6.99·10^30 | 9.59·10^36 | 50.9 |

* **A** — every empty cell can take any digit.
* **B** — every row is a permutation of its missing digits (row constraint built into the representation).
* **C** — every empty cell can take only the digits not used by its peers among the clues.

The landscape has exactly **one** point with f = 0 (unique solution) among 10^22 – 10^57 points; random grids have f ≈ 45–50. Fewer clues → larger landscape → harder for the search.

## 2.5 Algorithm — Breadth First Search with Backtracking

```
procedure BFS(puzzle):
    frontier ← FIFO queue containing puzzle
    while frontier is not empty:
        G ← frontier.pop_front()              # shallowest node first
        if G has no empty cell: return G      # goal test
        cell ← next empty cell                # row-major order
        D ← digits that do not appear in the row, column or box of cell
        if D is empty: continue               # dead end → branch abandoned (backtrack)
        for d in D:                           # only consistent children
            frontier.push_back(G with cell = d)
    return FAILURE
```

**Where is the backtracking?** A child is created only if the new digit is consistent with all constraints. A partial grid in which some empty cell has no possible digit is a *dead end*: it is dropped and the search continues with the remaining branches, so no node below an inconsistent partial grid is ever generated. (In DFS the same idea is "go back to the last decision"; in BFS all alternatives are already in the queue, so abandoning the branch is enough.)

**Cell order:** `--order row` (default) fills the first empty cell in row-major order — pure uninformed BFS. `--order mrv` fills the cell with the fewest possible digits (*minimum remaining values*) — an optional improvement shown for comparison.

### Properties

| | BFS on Sudoku |
|---|---|
| Branching factor | b ≤ 9 |
| Depth of the goal | d = e (all goals are at the deepest level, d = m) |
| Time | O(b^d) |
| Memory | O(b^d) — the whole frontier is kept in memory |
| Complete | yes (finite tree) |
| Optimal | yes, but every solution has the same depth, so optimality brings nothing here |

Because every solution lies at the deepest level, BFS has to generate the **entire** consistent search tree before it reaches the solution — the price is memory (see "max frontier" below). DFS would need only O(b·d) memory for the same tree.

## 2.6 Results

`python sudoku_bfs.py` (row order) and `python sudoku_bfs.py --order mrv`; times from a fast desktop CPU, on a laptop expect 3–4× more:

| Puzzle | Level | Depth | Row order: generated nodes | dead ends | max frontier | time | MRV: generated | max frontier |
|---|---|---|---|---|---|---|---|---|
| easy-1 | Easy | 51 | 4,632 | 1,371 | 738 | 0.005 s | 52 | 1 |
| easy-2 | Easy | 49 | 929 | 274 | 146 | 0.001 s | 50 | 1 |
| medium-1 | Medium | 56 | 36,239 | 13,341 | 7,862 | 0.04 s | 147 | 5 |
| medium-2 | Medium | 55 | 21,433 | 7,246 | 5,184 | 0.02 s | 445 | 17 |
| hard-1 Escargot | Hard | 58 | 18,885 | 5,376 | 1,716 | 0.02 s | 2,425 | 96 |
| hard-2 Everest | Hard | 60 | **2,068,781** | 705,261 | **356,812** | 2.3 s | 24,881 | 1,003 |

Observations:

* All six puzzles are solved and every solution has f = 0; `--all` confirms each puzzle has exactly one solution.
* With MRV the easy puzzles are solved with **no** branching at all (each step has a single candidate) — this is exactly the "naked single" technique.
* The hard puzzles force BFS to keep hundreds of thousands of partial grids in the queue — the typical weakness of BFS (exponential memory).
* Human difficulty and search difficulty are related but not identical: Escargot is "hard" for humans but the row-major tree happens to be small; Everest is hard for both.

### Example output (Everest)

```
Puzzle                   Solution
8 . . | . . . | . . .    8 1 2 | 7 5 3 | 6 4 9
. . 3 | 6 . . | . . .    9 4 3 | 6 8 2 | 1 7 5
. 7 . | . 9 . | 2 . .    6 7 5 | 4 9 1 | 2 8 3
------+-------+------    ------+-------+------
. 5 . | . . 7 | . . .    1 5 4 | 2 3 7 | 8 9 6
. . . | . 4 5 | 7 . .    3 6 9 | 8 4 5 | 7 2 1
. . . | 1 . . | . 3 .    2 8 7 | 1 6 9 | 5 3 4
------+-------+------    ------+-------+------
. . 1 | . . . | . 6 8    5 2 1 | 9 7 4 | 3 6 8
. . 8 | 5 . . | . 1 .    4 3 8 | 5 2 6 | 9 1 7
. 9 . | . . . | 4 . .    7 9 6 | 3 1 8 | 4 5 2
```

## 2.7 How to run

```bash
python sudoku_bfs.py                       # Easy, Medium and Hard puzzles from the bank
python sudoku_bfs.py --level medium        # one level only
python sudoku_bfs.py --order mrv           # most-constrained cell first
python sudoku_bfs.py --all                 # continue BFS and count all solutions
python sudoku_bfs.py --puzzle "..3.2.6..9..3.5..1..18.64....81.29..7.......8..67.82....26.95..8..2.3..9..5.1.3.."
python sudoku_bfs.py --file my_sudoku.txt  # 9 lines of 9 characters, '.' or '0' = empty
python sudoku_bfs.py --generate hard --seed 7
python sudoku_bfs.py --landscape
```

## References

* S. Russell, P. Norvig — *Artificial Intelligence: A Modern Approach*, ch. 3 (BFS) and ch. 6 (CSP, MRV).
* N. Musliu — *Problem Solving and Search in AI*, slides: Basic Concepts (Sudoku search space), Uninformed Search.
* B. Felgenhauer, F. Jarvis — *Enumerating possible Sudoku grids* (6.67 · 10^21 grids), 2005.
* Project Euler problem 96 (puzzle easy-2); A. Inkala — AI Escargot (2006), Everest (2012).
