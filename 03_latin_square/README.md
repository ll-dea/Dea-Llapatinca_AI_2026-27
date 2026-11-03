# 3. Latin Square — Iterative Deepening DFS (IDDFS) with Backtracking

> A Latin square is an n × n grid filled with n different numbers, each appearing exactly once in every row and every column. Given an input n, print an n × n matrix of the numbers 1..n in which each number appears exactly once in every row and every column.

**Example** — input `5`:

```
1 2 3 4 5
5 1 2 3 4
4 5 1 2 3
3 4 5 1 2
2 3 4 5 1
```

---

## 3.1 Modeling

| Element | Definition |
|---|---|
| **Given** | n |
| **Decision** | the number in each of the n² cells |
| **Hard constraints** | every row contains 1..n exactly once; every column contains 1..n exactly once |
| **Soft constraints** | none — satisfaction problem, any Latin square is a valid answer |

A Latin square exists for every n (e.g. the cyclic square `x(r,c) = ((c − r) mod n) + 1`), so the task is to *construct* one by search.

## 3.2 Representation

**Solution representation** — an n × n matrix `grid[r][c]`.

| | |
|---|---|
| **Variables** | x(r, c), r, c ∈ {0, …, n−1} → n² variables |
| **Domain** | D = {1, …, n} |
| **Constraints** | all-different(x(r,0), …, x(r,n−1)) for every row r<br>all-different(x(0,c), …, x(n−1,c)) for every column c |

**Problem representation (search state)** — a partially filled grid.

* **Initial state:** empty grid.
* **Action:** write a number into the next empty cell (row-major order).
* **Goal test:** all cells filled (constraints are checked on every step).
* **Depth of every goal:** d = n² — *all solutions are at the deepest level of the tree.*

### Reduced form (symmetry breaking, default)

Any Latin square can be turned into a *reduced* one — first row and first column equal to `1 2 … n` — by renaming the numbers and reordering the rows. So the program fixes the first row and column and searches only the remaining **(n−1)² cells** (depth of the goal d = (n−1)²). Use `--full` to search all n² cells.

## 3.3 Objective function

```
f(X) = Σ_r ( n − |distinct values in row r| )  +  Σ_c ( n − |distinct values in column c| )
```

f counts the repeated values. `f(X) = 0  ⇔  X is a Latin square.` With representation B below (rows are permutations) the row term is always 0 and only column conflicts remain. Every square printed by the program is checked with `objective()` and has f = 0.

## 3.4 Landscape (size of the search space)

`python latin_square.py 5 --landscape`:

| Representation | Formula | n = 5 | n = 6 |
|---|---|---|---|
| A — every cell any value | n^(n²) | 2.98 · 10^17 | 1.03 · 10^28 |
| B — every row a permutation | (n!)^n | 2.49 · 10^10 | 1.39 · 10^17 |
| A′ — reduced form, (n−1)² free cells | n^((n−1)²) | 1.53 · 10^11 | 2.84 · 10^19 |
| B′ — reduced form, rows are permutations | ((n−1)!)^(n−1) | 331,776 | 2.49 · 10^10 |
| **Number of Latin squares** L(n) = n!(n−1)!R(n) | | **161,280** | **8.13 · 10^8** |
| Number of reduced Latin squares R(n) | | 56 | 9,408 |

Only 5.4 · 10^−13 of representation A is feasible for n = 5. Random points of B have on average f ≈ 8 conflicts (n = 5); none of 2000 samples was a Latin square.

## 3.5 Algorithm — IDDFS with Backtracking

```
procedure IDDFS():
    for L = 0, 1, 2, …:
        result ← DLS(root, L)
        if result ≠ CUTOFF: return result

procedure DLS(node, L):                     # depth-limited DFS
    if node is a goal: return SOLUTION
    if depth(node) = L: return CUTOFF
    cutoff ← false
    (r, c) ← next empty cell
    for v in 1..n:
        if v already in row r or column c: continue      # prune
        x(r,c) ← v
        result ← DLS(child, L)
        if result = SOLUTION: return SOLUTION
        if result = CUTOFF: cutoff ← true
        x(r,c) ← empty                                   # BACKTRACK
    return CUTOFF if cutoff else FAILURE
```

* **Backtracking:** a value is placed only if it is not in the same row/column, so an inconsistent partial grid is never extended; when a cell has no value left the DLS returns to the previous cell and tries its next value.
* **CUTOFF vs FAILURE:** CUTOFF means "some branch was cut by the limit, a deeper search may succeed"; FAILURE means the complete tree was explored.
* **Value order** (`--order`): `natural` tries 1..n; `cyclic` starts with ((c − r) mod n) + 1. With `--full --order cyclic` IDDFS returns exactly the square of the example above.

### Properties

| | IDDFS |
|---|---|
| Branching factor | b ≤ n |
| Depth of the goal | d = (n−1)² (reduced) or n² (full) |
| Time | (d+1)·1 + d·b + (d−1)·b² + … + 1·b^d = O(b^d) |
| Memory | O(b·d) — only the current path |
| Complete | yes |
| Optimal | yes (for unit step cost) — but every solution has the same depth |

## 3.6 Results

`python latin_square.py N --verbose` (reduced form) and `python latin_square.py N --full`; times from a fast desktop CPU, on a laptop expect 3–4× more:

| n | depth d (reduced) | IDDFS nodes, reduced | time | depth d (full) | IDDFS nodes, full | time |
|---|---|---|---|---|---|---|
| 2 | 1 | 3 | 0.000 s | 4 | 21 | 0.000 s |
| 3 | 4 | 19 | 0.000 s | 9 | 326 | 0.000 s |
| 4 | 9 | 161 | 0.000 s | 16 | 24,861 | 0.02 s |
| **5** | 16 | **4,914** | 0.003 s | 25 | 13,505,923 | 10–45 s |
| 6 | 25 | 1,194,077 | 1–4 s | 36 | — | timeout |
| 7 | 36 | > 30 million (stopped at L = 20) | timeout | 49 | — | timeout |

Nodes per iteration for n = 5 (reduced): L = 0…15 visit 1, 5, 14, 28, 39, 64, 125, 201, 247, 323, 433, 569, 625, 681, 737, 793 nodes (all CUTOFF); the last iteration L = 16 finds the solution after only **29** nodes.

Output for `python latin_square.py 5`:

```
1 2 3 4 5
2 1 4 5 3
3 4 5 1 2
4 5 2 3 1
5 3 1 2 4

objective f = 0 (0 = Latin square)
iterations = 17  (last limit L = 16, nodes in last iteration = 29)
nodes visited = 4,914   time = 0.003s
```

### Discussion: IDDFS vs DFS for this problem

IDDFS is the best uninformed strategy when the goal is **shallow** (it is optimal like BFS but needs only O(b·d) memory like DFS). For the Latin square every goal lies at the **maximum depth** d = m, so:

* every iteration with L < d can never find a solution and must explore the *entire* tree up to depth L;
* the last iteration is just an ordinary DFS — it found the 5 × 5 square after 29 nodes, while the previous 16 iterations cost 4,885 nodes (≈ 170× more);
* the size of the tree grows like the number of partial Latin squares (R(7) = 16,942,080 reduced squares already), which is why IDDFS stops being practical at n ≈ 7.

For comparison, plain DFS with backtracking (`--algo dfs`) needs 29 nodes for n = 5, and on the full grid with the cyclic value order (`--algo dfs --full --order cyclic`) it never backtracks at all: n = 12 → 145 nodes, n = 50 → 2,501 nodes (= n² + 1). So for this problem IDDFS gives no benefit over DFS — a good illustration of when (not) to use iterative deepening.

## 3.7 How to run

```bash
python latin_square.py 5                     # IDDFS, reduced form
python latin_square.py                       # asks:  n = 
python latin_square.py 5 --verbose           # nodes of every iteration
python latin_square.py 5 --full --order cyclic   # gives exactly the example output (10-45 s)
python latin_square.py 50 --algo dfs --full --order cyclic   # DFS for comparison
python latin_square.py 5 --landscape         # search-space sizes
```

## References

* S. Russell, P. Norvig — *Artificial Intelligence: A Modern Approach*, ch. 3.4 (depth-limited search, IDDFS).
* N. Musliu — *Problem Solving and Search in AI*, slides: Uninformed Search.
* OEIS A000315 — number of reduced Latin squares of order n.
