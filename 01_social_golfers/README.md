# 1. Social Golfers Problem — DFS with Backtracking

> 32 golfers play golf once a week, always in groups of 4. For how many weeks can they play so that no two golfers play in the same group more than once?
>
> General form: can n = g × p golfers be scheduled into g groups of p golfers for w weeks so that no two golfers meet more than once?

Default instance: **g = 8 groups, p = 4 golfers, n = 32**.

---

## 1.1 Modeling

| Element | Definition |
|---|---|
| **Golfers** | G = {0, 1, …, n−1}, n = g·p |
| **Weeks** | W = {1, …, w} |
| **Groups** | {1, …, g} per week, each of size p |
| **Decision** | which golfer plays in which group in which week |
| **Hard constraint C1 (partition)** | every golfer plays in exactly one group per week |
| **Hard constraint C2 (socialisation)** | any two golfers are in the same group in at most one week |
| **Soft constraints** | none (this is a pure *satisfaction* problem; the optimisation version maximises w) |

### Upper bound on w

In every week a golfer meets p − 1 new golfers, and there are only n − 1 other golfers, so

```
w ≤ ⌊(n − 1) / (p − 1)⌋ = ⌊31 / 3⌋ = 10
```

10 weeks is known to be the optimum for 8-4 (an explicit 10-week schedule was first constructed by A. Aguado in 2004 using design theory).

## 1.2 Representation

**Solution representation** — a 3-D array

```
schedule[week][group][slot] = golfer          week ∈ 1..w, group ∈ 1..g, slot ∈ 1..p
```

| | |
|---|---|
| **Variables** | x(w, j, s) — the golfer in slot s of group j in week w → w·g·p = 32·w variables |
| **Domain** | D = {0, 1, …, 31} for every variable |
| **Constraints** | C1: x(w,·,·) is a permutation of 0..n−1 (all-different per week)<br>C2: for all golfers a ≠ b: \|{w : a and b in the same group of week w}\| ≤ 1 |

**Problem representation (search state)** — a *partial* schedule: the positions are filled in a fixed order (week by week, group by group). A node of the search tree is a partial schedule, a child assigns golfer(s) to the next free position, and a goal is a node in which all positions are filled and no constraint is violated.

The implementation keeps two bit-masks so that a constraint check is O(1):

* `used[week]` – golfers already placed in that week (C1)
* `met[a]` – golfers that golfer a already played with (C2)

## 1.3 Objective function

Satisfaction form — minimise the number of constraint violations:

```
f(S) =  Σ_{a<b}  max(0, m_ab(S) − 1)   +   Σ_w Σ_a | c_w(a) − 1 |
        └── repeated meetings (C2) ──┘     └── partition errors (C1) ──┘

m_ab(S) = number of weeks in which golfers a and b share a group
c_w(a)  = number of times golfer a appears in week w
```

`f(S) = 0  ⇔  S is a feasible schedule.`

Optimisation form — **maximise w** such that a schedule with f(S) = 0 exists.

The evaluation function used inside the search is the same as f restricted to the partial schedule: a node is kept only if its partial f is 0 (that is exactly what backtracking does). `objective()` in the code computes f for any schedule; every printed solution has f = 0.

## 1.4 Landscape (size of the search space)

The size of the search space depends on the representation (`python social_golfers.py --landscape`):

| Representation | Formula | w = 10 |
|---|---|---|
| A — one golfer per slot, domain 0..31 | n^(n·w) = 32^320 | **4.45 · 10^481** |
| B — every week is a permutation of the golfers (C1 built in) | (n!)^w | **1.59 · 10^354** |
| C — every week is a partition into unordered groups | [n! / ((p!)^g · g!)]^w | **5.37 · 10^197** |
| D — C + week 1 fixed + weeks unordered (symmetry) | [n!/((p!)^g g!)]^(w−1) / (w−1)! | **2.49 · 10^172** |

Number of ways to split 32 golfers into 8 unordered groups of 4:

```
32! / ((4!)^8 · 8!) = 5.93 · 10^19      (≈ the number of different weeks)
```

**Shape of the landscape.** One week covers 8·C(4,2) = 48 of the C(32,2) = 496 pairs; ten weeks need 480 distinct pairs, so a 10-week schedule uses 97 % of all pairs. Sampling 2000 random schedules of representation C gives:

| w | min f | mean f | max f | random schedules with f = 0 |
|---|---|---|---|---|
| 9 | 115 | 134.4 | 155 | 0 |
| 10 | 140 | 163.4 | 186 | 0 |

The feasible region is a vanishingly small part of the space and is surrounded by large plateaus of high f — random sampling (or exhaustive enumeration) is hopeless; the search has to be systematic and prune early.

## 1.5 Algorithm — Depth First Search with Backtracking

```
procedure DFS(level):
    if level = number of positions:          # all slots filled
        return SUCCESS                       # goal test
    for each child c of the current node (in the chosen order):
        if c violates C1 or C2: skip         # prune: branch is never generated
        apply c
        if DFS(level + 1) = SUCCESS: return SUCCESS
        undo c                               # BACKTRACK, try next child
    return FAIL                              # dead end
```

Backtracking = the constraints are checked on **partial** schedules; as soon as a partial schedule is infeasible the whole sub-tree below it is cut, and DFS returns to the most recent decision.

### Symmetry breaking (reduces the landscape, keeps at least one solution)

| | Rule | Why it is safe |
|---|---|---|
| S1 | golfers inside a group are increasing | the order inside a group is irrelevant |
| S2 | groups of a week are ordered by their smallest golfer (first slot = smallest free golfer) | group labels are irrelevant |
| S3 | week 1 = {0,1,2,3}, {4,5,6,7}, … | golfer labels are irrelevant |
| S4 | weeks ordered by the 2nd golfer of group 1 | week labels are irrelevant |

### Two child orderings (both are DFS with backtracking)

* **`lex`** (textbook): one golfer per tree level, children tried in increasing golfer number, S1–S4 active.
* **`freedom`** (default): one *pair* per tree level. The pairs are tried in order of minimal **freedom**, where the freedom of {a, b} is the number of golfers that neither a nor b has met yet (Triska & Musliu, 2012). Pairs that are close to running out of possible partners are scheduled first (*first-fail* principle). S3 is active. Only the order of the children changes — the algorithm is still a complete DFS with backtracking.

### Search-tree properties

| | `lex` | `freedom` |
|---|---|---|
| Depth of a goal (w = 10, week 1 fixed) | m = 9 · 32 = 288 | m = 9 · 16 = 144 |
| Branching factor | b ≤ 32 | b ≤ C(32,2) = 496 |
| Time (worst case) | O(b^m) | O(b^m) |
| Memory | O(b·m) — only the current path | O(b·m) |
| Complete / optimal | complete for finite trees, finds *a* solution | same |

## 1.6 Results

Python 3, single core, time limit 60 s per value of w (`python social_golfers.py --strategy lex --max`, `python social_golfers.py --max`). Times were measured on a fast desktop CPU; on a laptop they are roughly 3–4× longer, and the node counts reached before a timeout are correspondingly smaller:

| w | `lex` nodes | `lex` time | `freedom` nodes | `freedom` time |
|---|---|---|---|---|
| 2 | 32 | 0.000 s | 16 | 0.001 s |
| 5 | 128 | 0.000 s | 64 | 0.004 s |
| 6 | > 10 million | **timeout** | 80 | 0.005 s |
| 7 – 8 | – | – | 96 – 112 | 0.005 s |
| **9** | – | – | **128 (0 backtracks)** | **0.005 s** |
| 10 | – | – | > 20 million | timeout |

**Why does `lex` get stuck at week 6?** Taking the smallest golfer first builds weeks 2–5 entirely inside the halves {0..15} and {16..31}. After week 5 golfer 0 has already met all of 1..15 (and the same holds for every golfer in each half), so in week 6 a group can contain at most one golfer from each half — at most 2 golfers instead of 4. The mistake was made in week 2, but DFS only discovers it in week 6, so chronological backtracking has to exhaust an enormous sub-tree (*thrashing*).

**Why does `freedom` work?** Mixing pairs with the smallest freedom first prevents such closed blocks: the 9-week schedule is found with **zero backtracks**. For w = 10 (the proven optimum) the DFS did not finish within the time limit; Triska & Musliu report the same for complete backtracking — 8-4-10 was solved with design theory (Aguado) and later with a metaheuristic (local search).

### 9-week schedule found by DFS (f = 0)

```
         Group 1     | Group 2     | Group 3     | Group 4     | Group 5     | Group 6     | Group 7     | Group 8
Week 1   0,1,2,3     | 4,5,6,7     | 8,9,10,11   | 12,13,14,15 | 16,17,18,19 | 20,21,22,23 | 24,25,26,27 | 28,29,30,31
Week 2   0,4,8,12    | 1,5,9,13    | 2,6,10,14   | 3,7,11,15   | 16,20,24,28 | 17,21,25,29 | 18,22,26,30 | 19,23,27,31
Week 3   0,5,16,21   | 1,4,17,20   | 2,7,18,23   | 3,6,19,22   | 8,13,24,29  | 9,12,25,28  | 10,15,26,31 | 11,14,27,30
Week 4   0,6,26,28   | 1,7,27,29   | 2,4,24,30   | 3,5,25,31   | 8,14,18,20  | 9,15,19,21  | 10,12,16,22 | 11,13,17,23
Week 5   0,11,18,25  | 1,10,19,24  | 2,9,16,27   | 3,8,17,26   | 4,15,22,29  | 5,14,23,28  | 6,13,20,31  | 7,12,21,30
Week 6   0,7,10,13   | 1,6,11,12   | 2,5,8,15    | 3,4,9,14    | 16,23,26,29 | 17,22,27,28 | 18,21,24,31 | 19,20,25,30
Week 7   0,14,19,29  | 1,15,18,28  | 2,12,17,31  | 3,13,16,30  | 4,10,23,25  | 5,11,22,24  | 6,8,21,27   | 7,9,20,26
Week 8   0,15,20,27  | 1,14,21,26  | 2,13,22,25  | 3,12,23,24  | 4,11,16,31  | 5,10,17,30  | 6,9,18,29   | 7,8,19,28
Week 9   0,9,17,24   | 1,8,16,25   | 2,11,19,26  | 3,10,18,27  | 4,13,21,28  | 5,12,20,29  | 6,15,23,30  | 7,14,22,31
```

Other instances work too, e.g. Kirkman's schoolgirl problem (15 golfers, 5 groups of 3, 7 weeks) is solved by `lex` after ≈ 23 million nodes (0.5–2 min depending on the machine): `python social_golfers.py -g 5 -p 3 -w 7 --strategy lex --time-limit 300`.

## 1.7 How to run

```bash
python social_golfers.py                        # 8x4: increase w until DFS fails (freedom ordering)
python social_golfers.py -w 9                   # one run for exactly 9 weeks
python social_golfers.py --strategy lex --max   # textbook DFS, increasing w
python social_golfers.py -g 5 -p 3 -w 7 --strategy lex --time-limit 300
python social_golfers.py --landscape            # search-space sizes + sampled objective values
python social_golfers.py --help
```

Options: `-g`, `-p`, `-w`, `--max`, `--strategy {freedom,lex}`, `--time-limit SECONDS` (default 60), `--landscape`.

## References

* M. Triska, N. Musliu — *An effective greedy heuristic for the Social Golfer Problem*, Annals of Operations Research 194, 2012.
* CSPLib problem 010 — Social Golfers Problem.
* Z. Michalewicz, D. B. Fogel — *How to Solve It: Modern Heuristics*, ch. 1–3.
* N. Musliu — *Problem Solving and Search in AI*, slides: Basic Concepts, Uninformed Search.
