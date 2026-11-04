"""
Latin square - IDDFS with backtracking.

Input n, output an n x n grid with 1..n exactly once in every row and column.
Cells are filled one by one; a value is only tried if it is not already in the
row or column. IDDFS repeats a depth limited DFS with L = 0, 1, 2, ...

By default the first row and column are fixed to 1..n ("reduced form"), every
Latin square can be renamed into that form so nothing is lost.

    python latin_square.py 5
    python latin_square.py 5 --verbose
    python latin_square.py 5 --full --order cyclic   # gives the example from the assignment
    python latin_square.py 50 --algo dfs --full --order cyclic
    python latin_square.py 5 --landscape
"""

import argparse
import math
import random
import sys
import time

sys.setrecursionlimit(100000)

SOLUTION, CUTOFF, FAILURE, TIMEOUT = "solution", "cutoff", "failure", "timeout"

# number of reduced Latin squares, OEIS A000315
REDUCED_COUNT = {1: 1, 2: 1, 3: 1, 4: 4, 5: 56, 6: 9408, 7: 16942080,
                 8: 535281401856, 9: 377597570964258816,
                 10: 7580721483160132811489280,
                 11: 5363937773277371298119673540771840}


class Timeout(Exception):
    pass


class LatinSquare:
    def __init__(self, n, reduced=True, order="natural", time_limit=120):
        self.n = n
        self.order = order
        self.time_limit = time_limit
        self.grid = [[0] * n for _ in range(n)]
        self.row_used = [0] * n   # bitmask of values in row r
        self.col_used = [0] * n   # bitmask of values in column c

        if reduced:
            for c in range(n):
                self.set(0, c, c + 1)
            for r in range(1, n):
                self.set(r, 0, r + 1)
            self.cells = [(r, c) for r in range(1, n) for c in range(1, n)]
        else:
            self.cells = [(r, c) for r in range(n) for c in range(n)]
        self.depth = len(self.cells)   # every solution is at this depth

        self.nodes = 0         # nodes of the current iteration
        self.total_nodes = 0
        self.iterations = []   # (limit, nodes, result)
        self.start = None
        self.elapsed = 0

    def set(self, r, c, v):
        self.grid[r][c] = v
        self.row_used[r] |= 1 << v
        self.col_used[c] |= 1 << v

    def unset(self, r, c):
        v = self.grid[r][c]
        self.grid[r][c] = 0
        self.row_used[r] &= ~(1 << v)
        self.col_used[c] &= ~(1 << v)

    def values(self, r, c):
        n = self.n
        if self.order == "cyclic":
            # start from (c - r) mod n, the value of the cyclic square
            s = (c - r) % n
            return [(s + k) % n + 1 for k in range(n)]
        return range(1, n + 1)

    def allowed(self, r, c, v):
        return not (self.row_used[r] >> v & 1 or self.col_used[c] >> v & 1)

    def dls(self, k, limit):
        """Depth limited DFS, k = number of cells filled so far."""
        self.nodes += 1
        if k == self.depth:
            return SOLUTION
        if k == limit:
            return CUTOFF
        if self.nodes & 0xFFFF == 0 and self.time_limit and time.time() - self.start > self.time_limit:
            raise Timeout

        r, c = self.cells[k]
        cutoff = False
        for v in self.values(r, c):
            if not self.allowed(r, c, v):
                continue
            self.set(r, c, v)
            result = self.dls(k + 1, limit)
            if result == SOLUTION:
                return SOLUTION
            if result == CUTOFF:
                cutoff = True
            self.unset(r, c)   # backtrack
        return CUTOFF if cutoff else FAILURE

    def iddfs(self, verbose=False):
        self.start = time.time()
        result = FAILURE
        try:
            for limit in range(self.depth + 1):
                self.nodes = 0
                result = self.dls(0, limit)
                self.total_nodes += self.nodes
                self.iterations.append((limit, self.nodes, result))
                if verbose:
                    print(f"  L = {limit:<4} nodes = {self.nodes:<12,} -> {result}")
                if result != CUTOFF:
                    break
        except Timeout:
            self.total_nodes += self.nodes
            self.iterations.append((limit, self.nodes, TIMEOUT))
            result = TIMEOUT
        self.elapsed = time.time() - self.start
        return result

    def dfs(self):
        """Plain DFS = one DLS without a limit."""
        self.start = time.time()
        self.nodes = 0
        try:
            result = self.dls(0, float("inf"))
        except Timeout:
            result = TIMEOUT
        self.total_nodes = self.nodes
        self.elapsed = time.time() - self.start
        return result


def objective(grid):
    """Repeated values in rows + repeated values in columns. 0 = Latin square."""
    n = len(grid)
    f = 0
    for r in range(n):
        f += n - len(set(grid[r]))
    for c in range(n):
        f += n - len({grid[r][c] for r in range(n)})
    return f


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

    # objective of random grids where every row is a permutation
    rng = random.Random(seed)
    vals = []
    for _ in range(samples):
        grid = []
        for _ in range(n):
            row = list(range(1, n + 1))
            rng.shuffle(row)
            grid.append(row)
        vals.append(objective(grid))
    vals.sort()
    print(f"\n  objective over {samples} random grids of B: min={vals[0]} "
          f"mean={sum(vals) / len(vals):.2f} max={vals[-1]}  feasible={vals.count(0)}")


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
                    help="search all n*n cells (no reduced form)")
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

    s = LatinSquare(n, reduced=not args.full, order=args.order, time_limit=args.time_limit)
    print(f"Latin square n = {n}, algorithm = {args.algo}, "
          f"{'full grid' if args.full else 'reduced form'}, value order = {args.order}")
    print(f"free cells (depth of the goal) = {s.depth}\n")

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
    if result == TIMEOUT and args.algo == "iddfs":
        print("\nIDDFS explores the whole tree up to depth L-1 before reaching depth L;\n"
              "all Latin squares lie at the deepest level, so this grows like the number\n"
              "of partial Latin squares. Try a smaller n, or compare with --algo dfs --full --order cyclic.")
    elif result == TIMEOUT:
        print("\nDFS thrashes for this n; try --full --order cyclic.")


if __name__ == "__main__":
    main()
