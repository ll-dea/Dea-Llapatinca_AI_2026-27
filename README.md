# Artificial Intelligence 2026/27 — Assignment 1

## Uninformed Search Techniques

**Author:** Dea Llapatinca

This repository contains the solution of the first semester assignment. For every problem the README in its folder contains the **model**, the **representation** (variables, domains, constraints), the **objective function**, the **landscape** (size of the search space) and the **results**; the Python program implements the required search algorithm.

| # | Problem | Algorithm | Folder | Main result |
|---|---|---|---|---|
| 1 | Social Golfers (32 golfers, 8 groups of 4) | DFS + backtracking | [`01_social_golfers`](01_social_golfers/) | 9-week schedule in < 0.1 s with 0 backtracks (optimum is 10) |
| 2 | Sudoku (Easy / Medium / Hard) | BFS + backtracking | [`02_sudoku`](02_sudoku/) | all 6 puzzles solved, incl. *AI Escargot* and *Everest* |
| 3 | Latin Square (input n) | IDDFS + backtracking | [`03_latin_square`](03_latin_square/) | n = 5 in 4,914 nodes; analysis of why IDDFS costs more than DFS here |
| 4 | Search trees: 8-Puzzle, Missionaries & Cannibals, Rotating Workforce Scheduling | BFS / DFS / DFS + backtracking | [`04_search_trees`](04_search_trees/) | formulations + generated search-tree pictures |

## Requirements

* Python 3.8 or newer — **no external packages** (only the standard library).
* Optional: [Graphviz](https://graphviz.org/) (`dot`) to re-draw the search-tree pictures of part 4. The pictures are already in `04_search_trees/img/`.

## Quick start

```bash
# 1. Social Golfers - DFS with backtracking
cd 01_social_golfers
python social_golfers.py                 # 8 groups x 4: largest number of weeks
python social_golfers.py --landscape     # size of the search space

# 2. Sudoku - BFS with backtracking
cd ../02_sudoku
python sudoku_bfs.py                     # Easy, Medium and Hard puzzles
python sudoku_bfs.py --level hard --order mrv

# 3. Latin square - IDDFS with backtracking
cd ../03_latin_square
python latin_square.py 5 --verbose

# 4. Search trees
cd ../04_search_trees
python eight_puzzle.py
python missionaries_cannibals.py
python rotating_workforce.py
```

Every program has `--help`.

## Structure

```
.
├── README.md
├── 01_social_golfers/
│   ├── README.md              model, representation, objective, landscape, results
│   └── social_golfers.py      DFS with backtracking (lex and min-freedom ordering)
├── 02_sudoku/
│   ├── README.md
│   ├── sudoku_bfs.py          BFS with backtracking
│   └── puzzles.py             Easy/Medium/Hard bank, difficulty rater, generator
├── 03_latin_square/
│   ├── README.md
│   └── latin_square.py        IDDFS (+ plain DFS for comparison)
└── 04_search_trees/
    ├── README.md              formulations and pictures of the search trees
    ├── eight_puzzle.py
    ├── missionaries_cannibals.py
    ├── rotating_workforce.py
    ├── tree_tools.py          search-tree recorder + Graphviz export
    └── img/                   generated pictures (.png, .svg, .dot)
```

## Common concepts

**Representation** — encodes the candidate solutions (variables + domains); the size of the search space is determined by the representation, not by the problem itself.
**Objective function** — the mathematical statement of the goal; here every problem is a satisfaction problem, so the objective is "number of violated constraints = 0".
**Evaluation function** — maps every candidate (also partial ones) to a number; used by the search to accept or reject nodes.
**Landscape** — the set of all candidates of a representation together with their evaluation values.
**Backtracking** — constraints are checked on partial solutions; an inconsistent partial solution is never extended, the search returns to the last decision.

| | BFS | DFS | IDDFS |
|---|---|---|---|
| Complete | yes (finite b) | yes, if the tree is finite | yes |
| Optimal | yes (unit cost) | no | yes (unit cost) |
| Time | O(b^d) | O(b^m) | O(b^d) |
| Memory | O(b^d) | O(b·m) | O(b·d) |
| Used for | Sudoku | Social Golfers, RWS | Latin square |

b = branching factor, d = depth of the shallowest goal, m = maximum depth. In problems 1–3 every solution lies at the maximum depth (d = m), which is why the measured differences come mostly from memory (BFS) and repeated work (IDDFS).

## Literature

* S. Russell, P. Norvig — *Artificial Intelligence: A Modern Approach*, ch. 3.
* Z. Michalewicz, D. B. Fogel — *How to Solve It: Modern Heuristics*, ch. 1–3.
* N. Musliu — *Problem Solving and Search in Artificial Intelligence* (slides: Basic Concepts, Uninformed Search).
