"""
Sudoku solver - BFS with backtracking.

The grid is a string of 81 chars ('.' = empty). A node of the search tree is a
partial grid, its children fill one more cell. BFS uses a FIFO queue, so the
shallowest nodes are expanded first. Children that break a row/column/box
constraint are never created (backtracking), a node with no valid children is
simply dropped.

    python sudoku_bfs.py                   # easy, medium and hard puzzles from puzzles.py
    python sudoku_bfs.py --level hard
    python sudoku_bfs.py --order mrv       # fill the most constrained cell first
    python sudoku_bfs.py --puzzle "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79"
    python sudoku_bfs.py --file my_sudoku.txt
    python sudoku_bfs.py --generate medium --seed 7
    python sudoku_bfs.py --landscape
"""

import argparse
import math
import random
import time
from collections import deque

from puzzles import PUZZLES, PEERS, UNITS, DIGITS, normalize, rate, generate, candidates


def next_cell(grid, order):
    """Which empty cell to fill next and the digits allowed there."""
    if order == "row":
        i = grid.index(".")
        return i, sorted(candidates(grid, i))
    # mrv: the empty cell with the fewest candidates
    best_i, best_c = None, None
    for i in range(81):
        if grid[i] == ".":
            c = candidates(grid, i)
            if best_c is None or len(c) < len(best_c):
                best_i, best_c = i, c
                if len(c) <= 1:
                    break
    return best_i, sorted(best_c)


def bfs(puzzle, order="row", find_all=False, max_frontier=5_000_000):
    stats = {"generated": 1, "expanded": 0, "dead_ends": 0,
             "max_frontier": 1, "depth": puzzle.count(".")}
    start = time.time()

    # clues that already clash -> no solution
    for i in range(81):
        if puzzle[i] != "." and any(puzzle[j] == puzzle[i] for j in PEERS[i]):
            stats["time"] = 0.0
            return [], stats

    frontier = deque([puzzle])
    solutions = []
    while frontier:
        grid = frontier.popleft()
        if "." not in grid:
            solutions.append(grid)
            if not find_all:
                break
            continue

        stats["expanded"] += 1
        cell, digits = next_cell(grid, order)
        if not digits:
            stats["dead_ends"] += 1
            continue
        for d in digits:
            frontier.append(grid[:cell] + d + grid[cell + 1:])
            stats["generated"] += 1
        stats["max_frontier"] = max(stats["max_frontier"], len(frontier))
        if len(frontier) > max_frontier:
            raise MemoryError("frontier too large - BFS ran out of memory budget")

    stats["time"] = time.time() - start
    return solutions, stats


def objective(grid, puzzle=None):
    """For every row/column/box: 9 - number of different digits. 0 = solved."""
    f = sum(9 - len({grid[i] for i in unit if grid[i] != "."}) for unit in UNITS)
    if puzzle:
        f += sum(1 for a, b in zip(puzzle, grid) if a != "." and a != b)   # changed clues
    return f


def sci(x):
    if x == 0:
        return "0"
    e = math.floor(math.log10(x))
    return f"{x / 10 ** e:.2f}e{e}"


def landscape(puzzle, samples=2000, seed=1):
    empty = [i for i in range(81) if puzzle[i] == "."]
    e = len(empty)
    a = 9 ** e
    b = 1
    for unit in UNITS[:9]:
        missing = sum(1 for i in unit if puzzle[i] == ".")
        b *= math.factorial(missing)
    c = 1
    for i in empty:
        c *= len(candidates(puzzle, i))
    print(f"  empty cells e = {e}, clues = {81 - e}, level = {rate(puzzle)}")
    print(f"  A  every empty cell any digit           9^e              = {sci(a)}")
    print(f"  B  every row a permutation (clues kept) prod(missing_r!) = {sci(b)}")
    print(f"  C  only digits allowed by the clues     prod |D(cell)|   = {sci(c)}")

    # objective of random grids where every row is a permutation
    rng = random.Random(seed)
    vals = []
    for _ in range(samples):
        g = list(puzzle)
        for unit in UNITS[:9]:
            missing = [d for d in DIGITS if d not in [g[i] for i in unit]]
            rng.shuffle(missing)
            for i in unit:
                if g[i] == ".":
                    g[i] = missing.pop()
        vals.append(objective("".join(g)))
    vals.sort()
    print(f"  objective over {samples} random grids of B: min={vals[0]} "
          f"mean={sum(vals) / len(vals):.1f} max={vals[-1]}")


def show(grid):
    lines = []
    for r in range(9):
        if r in (3, 6):
            lines.append("------+-------+------")
        row = grid[r * 9:(r + 1) * 9]
        lines.append(" ".join(row[0:3]) + " | " + " ".join(row[3:6]) + " | " + " ".join(row[6:9]))
    return "\n".join(lines)


def side_by_side(left, right):
    a, b = show(left).split("\n"), show(right).split("\n")
    out = [f"{'Puzzle':<25}Solution"]
    out += [f"{x:<25}{y}" for x, y in zip(a, b)]
    return "\n".join(out)


def solve(name, puzzle, order, find_all):
    print("=" * 60)
    print(f"{name}   clues={81 - puzzle.count('.')}  rated={rate(puzzle)}  order={order}")
    print("=" * 60)
    try:
        sols, st = bfs(puzzle, order, find_all)
    except MemoryError as err:
        print(f"  {err}\n")
        return
    if not sols:
        print("  no solution\n")
        return
    print(side_by_side(puzzle, sols[0]))
    print(f"\n  objective f = {objective(sols[0], puzzle)} (0 = solved)")
    print(f"  depth of goal = {st['depth']}  generated = {st['generated']:,}  "
          f"expanded = {st['expanded']:,}  dead ends = {st['dead_ends']:,}")
    print(f"  max frontier (memory) = {st['max_frontier']:,}  time = {st['time']:.3f}s")
    if find_all:
        print(f"  number of solutions = {len(sols)}")
    print()


def main():
    ap = argparse.ArgumentParser(description="Sudoku solver - BFS with backtracking")
    ap.add_argument("--level", choices=["easy", "medium", "hard", "all"], default="all")
    ap.add_argument("--puzzle", help="81-character puzzle, '.' or '0' for empty cells")
    ap.add_argument("--file", help="text file with a puzzle (9 lines or one line)")
    ap.add_argument("--generate", choices=["easy", "medium", "hard"],
                    help="generate a random puzzle of this level and solve it")
    ap.add_argument("--seed", type=int, default=None, help="seed for --generate")
    ap.add_argument("--order", choices=["row", "mrv"], default="row",
                    help="which empty cell to fill next (default: row)")
    ap.add_argument("--all", action="store_true", help="continue the BFS and count all solutions")
    ap.add_argument("--landscape", action="store_true", help="print search-space sizes")
    args = ap.parse_args()

    jobs = []
    if args.puzzle:
        jobs.append(("custom puzzle", normalize(args.puzzle)))
    elif args.file:
        with open(args.file, encoding="utf-8") as fh:
            jobs.append((args.file, normalize(fh.read())))
    elif args.generate:
        clues = {"easy": 32, "medium": 26, "hard": 24}[args.generate]
        p = generate(args.generate, seed=args.seed, clues=clues)
        print(f"generated {args.generate} puzzle: {p}\n")
        jobs.append((f"generated {args.generate}", p))
    else:
        levels = ["easy", "medium", "hard"] if args.level == "all" else [args.level]
        for lv in levels:
            jobs.extend(PUZZLES[lv])

    if args.landscape:
        print("Full 9x9 grid: 9^81 =", sci(9 ** 81), "| valid complete Sudoku grids = 6.67e21\n")
        for name, p in jobs:
            print(name)
            landscape(p)
            print()
        return

    for name, p in jobs:
        solve(name, p, args.order, args.all)


if __name__ == "__main__":
    main()
