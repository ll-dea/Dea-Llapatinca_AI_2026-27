"""
Latin Square - Iterative Deepening Depth First Search (IDDFS) + Backtracking
============================================================================

A Latin square of order n is an n x n grid filled with the numbers 1..n so
that every number appears exactly once in every row and every column.
Input: n.  Output: one n x n Latin square.

Representation
--------------
    grid[r][c] in {1..n}         variable x(r, c), domain {1..n}

Constraints
-----------
    all-different(row r)     for every r
    all-different(column c)  for every c

Search tree
-----------
    root  = empty grid (or the reduced form, see below)
    level k fills the k-th cell in row-major order
    goal  = all cells filled  ->  depth of every goal = number of free cells

IDDFS runs a depth-limited DFS (DLS) with limit L = 0, 1, 2, ... until a
goal is found.  DLS returns
    SOLUTION  - goal found
    CUTOFF    - some node was cut at the depth limit (try a larger L)
    FAILURE   - the whole tree was explored, no solution exists
Backtracking: a value is placed only if it does not already appear in the
row or column; when a cell has no value left DLS goes back to the previous
cell and tries its next value.

Reduced form (symmetry breaking, default on): every Latin square can be
turned into one whose first row and first column are 1 2 ... n (relabel
the numbers, reorder the rows).  So it is enough to search only the
(n-1)^2 remaining cells.

Usage
-----
    python latin_square.py 5
    python latin_square.py               # asks for n
    python latin_square.py 5 --verbose   # nodes of every IDDFS iteration
    python latin_square.py 5 --full --order cyclic   # no symmetry breaking
    python latin_square.py 50 --algo dfs --full --order cyclic
    python latin_square.py 5 --landscape
"""

import argparse
import math
import random
import sys
import time

sys.setrecursionlimit(100000)

SOLUTION, CUTOFF, FAILURE = "solution", "cutoff", "failure"

# number of reduced Latin squares R(n)  (OEIS A000315)
REDUCED_COUNT = {1: 1, 2: 1, 3: 1, 4: 4, 5: 56, 6: 9408, 7: 16942080,
                 8: 535281401856, 9: 377597570964258816,
                 10: 7580721483160132811489280,
                 11: 5363937773277371298119673540771840}


class SearchTimeout(Exception):
    pass


class LatinSquareSearch:
    def __init__(self, n, reduced=True, order="natural", time_limit=120):
        self.n = n
        self.order = order
        self.time_limit = time_limit
        self.grid = [[0] * n for _ in range(n)]
        self.row_used = [0] * n          # bitmask of numbers used in row r
        self.col_used = [0] * n          # bitmask of numbers used in column c

        if reduced:
            for c in range(n):
                self._set(0, c, c + 1)
            for r in range(1, n):
                self._set(r, 0, r + 1)
            self.cells = [(r, c) for r in range(1, n) for c in range(1, n)]
        else:
            self.cells = [(r, c) for r in range(n) for c in range(n)]
        self.depth_of_goal = len(self.cells)

        self.nodes = 0                   # nodes visited in the current iteration
        self.total_nodes = 0
        self.iterations = []             # (limit, nodes, result)
        self.start = None

    # ------------------------------------------------------------ #
    def _set(self, r, c, v):
        self.grid[r][c] = v
        self.row_used[r] |= 1 << v
        self.col_used[c] |= 1 << v

    def _unset(self, r, c):
        v = self.grid[r][c]
        self.grid[r][c] = 0
        self.row_used[r] &= ~(1 << v)
        self.col_used[c] &= ~(1 << v)

    def _values(self, r, c):
        """Values tried for cell (r, c), in order."""
        n = self.n
        if self.order == "cyclic":                     # start with (c - r) mod n
            s = (c - r) % n
            return [((s + k) % n) + 1 for k in range(n)]
        return range(1, n + 1)

    def _consistent(self, r, c, v):
        return not (self.row_used[r] >> v & 1 or self.col_used[c] >> v & 1)

    # ------------------------------------------------------------ #
    # depth-limited DFS with backtracking
    # ------------------------------------------------------------ #
    def dls(self, k, limit):
        """k = depth of the current node = number of filled free cells."""
        self.nodes += 1
        if k == self.depth_of_goal:
            return SOLUTION                            # goal test
        if k == limit:
            return CUTOFF                              # depth limit reached
        if self.nodes & 0xFFFF == 0 and self.time_limit and \
                time.time() - self.start > self.time_limit:
            raise SearchTimeout

        r, c = self.cells[k]
        cutoff = False
        for v in self._values(r, c):
            if not self._consistent(r, c, v):          # prune -> never generated
                continue
            self._set(r, c, v)
            result = self.dls(k + 1, limit)
            if result == SOLUTION:
                return SOLUTION
            if result == CUTOFF:
                cutoff = True
            self._unset(r, c)                          # backtrack
        return CUTOFF if cutoff else FAILURE

    def iddfs(self, verbose=False):
        self.start = time.time()
        result = FAILURE
        try:
            for limit in range(0, self.depth_of_goal + 1):
                self.nodes = 0
                result = self.dls(0, limit)
                self.total_nodes += self.nodes
                self.iterations.append((limit, self.nodes, result))
                if verbose:
                    print(f"  L = {limit:<4} nodes = {self.nodes:<12,} -> {result}")
                if result != CUTOFF:
                    break
        except SearchTimeout:
            self.total_nodes += self.nodes
            self.iterations.append((limit, self.nodes, "timeout"))
            result = "timeout"
        self.elapsed = time.time() - self.start
        return result

    def dfs(self):
        """Plain DFS with backtracking (= DLS with an infinite limit)."""
        self.start = time.time()
        self.nodes = 0
        try:
            result = self.dls(0, float("inf"))
        except SearchTimeout:
            result = "timeout"
        self.total_nodes = self.nodes
        self.elapsed = time.time() - self.start
        return result


# ====================================================================== #
# objective function
# ====================================================================== #
def objective(grid):
    """f(X) = sum_rows (n - |distinct values|) + sum_cols (n - |distinct values|)
    = number of repeated values.  f = 0  <=>  X is a Latin square."""
    n = len(grid)
    f = 0
    for r in range(n):
        f += n - len(set(grid[r]))
    for c in range(n):
        f += n - len({grid[r][c] for r in range(n)})
    return f


# ====================================================================== #
# landscape
# ====================================================================== #
def sci(x):
    if x == 0:
        return "0"
    e = math.floor(math.log10(x))
    return f"{x / 10 ** e:.2f}e{e}" if e >= 6 else f"{x:,}"


def landscape(n, samples=2000, seed=1):
    print(f"Landscape for n = {n}\n")
    print(f"  A  every cell a value 1..n                 n^(n^2)         = {sci(n ** (n * n))}")
    print(f"  B  every row a permutation                 (n!)^n          = {sci(math.factorial(n) ** n)}")
    print(f"  A' reduced form, (n-1)^2 free cells        n^((n-1)^2)     = {sci(n ** ((n - 1) ** 2))}")
    print(f"  B' reduced form, rows = permutations       ((n-1)!)^(n-1)  = {sci(math.factorial(n - 1) ** (n - 1))}")
    if n in REDUCED_COUNT:
        red = REDUCED_COUNT[n]
        total = math.factorial(n) * math.factorial(n - 1) * red
        print(f"\n  Latin squares of order n        L(n) = n!(n-1)!R(n) = {sci(total)}")
        print(f"  reduced Latin squares           R(n)               = {sci(red)}")
        print(f"  share of A that is feasible     L(n) / n^(n^2)     = {total / n ** (n * n):.3e}")

    rng = random.Random(seed)
    vals = []
    for _ in range(samples):                         # random points of B
        grid = []
        for _ in range(n):
            row = list(range(1, n + 1))
            rng.shuffle(row)
            grid.append(row)
        vals.append(objective(grid))
    vals.sort()
    print(f"\n  objective over {samples} random grids of B: min={vals[0]} "
          f"mean={sum(vals) / len(vals):.2f} max={vals[-1]}  "
          f"feasible={sum(1 for v in vals if v == 0)}")


# ====================================================================== #
def print_grid(grid):
    width = len(str(len(grid)))
    for row in grid:
        print(" ".join(f"{v:>{width}}" for v in row))


def main():
    ap = argparse.ArgumentParser(description="Latin square - IDDFS with backtracking")
    ap.add_argument("n", type=int, nargs="?", help="order of the square")
    ap.add_argument("--algo", choices=["iddfs", "dfs"], default="iddfs",
                    help="iddfs (default) or plain DFS for comparison")
    ap.add_argument("--full", action="store_true",
                    help="search all n*n cells (no reduced-form symmetry breaking)")
    ap.add_argument("--order", choices=["natural", "cyclic"], default="natural",
                    help="value order: 1..n (natural) or starting at (c-r) mod n (cyclic)")
    ap.add_argument("--time-limit", type=float, default=120, help="seconds (default 120)")
    ap.add_argument("--verbose", action="store_true", help="print every IDDFS iteration")
    ap.add_argument("--landscape", action="store_true", help="print search-space sizes")
    args = ap.parse_args()

    n = args.n
    if n is None:
        n = int(input("n = "))
    if n < 1:
        sys.exit("n must be >= 1")

    if args.landscape:
        landscape(n)
        return

    s = LatinSquareSearch(n, reduced=not args.full, order=args.order,
                          time_limit=args.time_limit)
    print(f"Latin square n = {n}, algorithm = {args.algo}, "
          f"{'full grid' if args.full else 'reduced form'}, value order = {args.order}")
    print(f"free cells (depth of the goal) = {s.depth_of_goal}\n")

    result = s.iddfs(args.verbose) if args.algo == "iddfs" else s.dfs()

    if result == SOLUTION:
        if args.verbose:
            print()
        print_grid(s.grid)
        print(f"\nobjective f = {objective(s.grid)} (0 = Latin square)")
    else:
        print(f"result: {result}")
    if args.algo == "iddfs":
        last = s.iterations[-1]
        print(f"iterations = {len(s.iterations)}  (last limit L = {last[0]}, "
              f"nodes in last iteration = {last[1]:,})")
    print(f"nodes visited = {s.total_nodes:,}   time = {s.elapsed:.3f}s")
    if result == "timeout" and args.algo == "iddfs":
        print("\nIDDFS explores the whole tree up to depth L-1 before reaching depth L;\n"
              "all Latin squares lie at the deepest level, so this grows like the number\n"
              "of partial Latin squares. Try a smaller n, or compare with --algo dfs --full --order cyclic.")
    elif result == "timeout":
        print("\nDFS thrashes for this n; try --full --order cyclic.")


if __name__ == "__main__":
    main()
