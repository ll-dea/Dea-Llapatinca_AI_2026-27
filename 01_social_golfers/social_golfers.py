"""
Social Golfers Problem - DFS with backtracking.

n = g*p golfers play once a week in g groups of p. Find a schedule for w weeks
where no two golfers play in the same group more than once.

    python social_golfers.py                   # 8 groups x 4, increase weeks until it fails
    python social_golfers.py -w 9              # exactly 9 weeks
    python social_golfers.py --strategy lex --max
    python social_golfers.py --landscape
"""

import argparse
import math
import random
import sys
import time
from itertools import combinations

sys.setrecursionlimit(10000)


def popcount(x):
    return bin(x).count("1")


class Timeout(Exception):
    pass


class SocialGolfersDFS:
    """
    schedule[week][group] = list of golfers.

    Golfers are stored as bits, so checking if two golfers already met or if a golfer
    already plays this week is a single AND.

    Two ways to order the children of a node (both are plain DFS with backtracking):
      lex     - one golfer per level, smallest golfer first, with symmetry breaking
      freedom - one pair of golfers per level, the pair with the fewest common
                unmet golfers first (Triska & Musliu 2012)
    """

    def __init__(self, g, p, w, strategy="freedom", time_limit=60):
        self.g = g
        self.p = p
        self.w = w
        self.n = g * p
        self.all_golfers = (1 << self.n) - 1
        self.strategy = strategy
        self.time_limit = time_limit

        self.schedule = [[[] for _ in range(g)] for _ in range(w)]
        self.met = [0] * self.n   # met[a] = golfers a already played with
        self.used = [0] * w       # used[week] = golfers already placed in that week

        self.nodes = 0
        self.backtracks = 0
        self.elapsed = 0
        self.start = None

        # one entry per level of the search tree: (week, group, how many golfers to add)
        if strategy == "lex":
            step = [1] * p
        else:
            step = [2] * (p // 2) + [1] * (p % 2)
        self.levels = [(wk, gr, k) for wk in range(w) for gr in range(g) for k in step]

    def place(self, week, group, golfer):
        for m in self.schedule[week][group]:
            self.met[m] |= 1 << golfer
            self.met[golfer] |= 1 << m
        self.schedule[week][group].append(golfer)
        self.used[week] |= 1 << golfer

    def remove(self, week, group):
        golfer = self.schedule[week][group].pop()
        for m in self.schedule[week][group]:
            self.met[m] &= ~(1 << golfer)
            self.met[golfer] &= ~(1 << m)
        self.used[week] &= ~(1 << golfer)

    def free_golfers(self, week, group):
        # not playing this week yet and never met anyone already in the group
        free = self.all_golfers & ~self.used[week]
        for m in self.schedule[week][group]:
            free &= ~self.met[m]
        return free

    def children(self, week, group, k):
        free = self.free_golfers(week, group)

        if self.strategy == "lex":
            members = self.schedule[week][group]
            if not members:
                free &= -free   # first slot of a group: only the smallest free golfer
            else:
                free &= ~((1 << (members[-1] + 1)) - 1)   # keep golfers increasing in a group
            if group == 0 and len(members) == 1 and week > 0:
                # weeks ordered by the partner of golfer 0
                prev = self.schedule[week - 1][0][1]
                free &= ~((1 << (prev + 1)) - 1)
            while free:
                low = free & -free
                yield (low.bit_length() - 1,)
                free ^= low
            return

        golfers = [i for i in range(self.n) if free >> i & 1]
        if k == 1:
            golfers.sort(key=lambda a: (popcount(self.all_golfers & ~self.met[a]), a))
            for a in golfers:
                yield (a,)
            return

        pairs = []
        for i, a in enumerate(golfers):
            for b in golfers[i + 1:]:
                if self.met[a] >> b & 1:
                    continue
                unmet = self.all_golfers & ~self.met[a] & ~self.met[b] & ~(1 << a) & ~(1 << b)
                pairs.append((popcount(unmet), a, b))
        pairs.sort()
        for _, a, b in pairs:
            yield (a, b)

    def dfs(self, level):
        if level == len(self.levels):
            return True
        if self.time_limit and time.time() - self.start > self.time_limit:
            raise Timeout

        week, group, k = self.levels[level]
        for child in self.children(week, group, k):
            self.nodes += 1
            for golfer in child:
                self.place(week, group, golfer)
            if self.dfs(level + 1):
                return True
            for _ in child:
                self.remove(week, group)   # backtrack

        self.backtracks += 1
        return False

    def solve(self):
        """True = found, False = no schedule, None = time limit."""
        self.start = time.time()
        level = 0
        if self.w > 0:
            # week 1 can always be {0..p-1}, {p..2p-1}, ... (golfers are interchangeable)
            for gr in range(self.g):
                for s in range(self.p):
                    self.place(0, gr, gr * self.p + s)
            while level < len(self.levels) and self.levels[level][0] == 0:
                level += 1
        try:
            found = self.dfs(level)
        except Timeout:
            found = None
        self.elapsed = time.time() - self.start
        return found


def objective(schedule, n):
    """Number of repeated meetings + golfers missing/doubled in a week. 0 = valid."""
    meetings = {}
    partition_errors = 0
    for week in schedule:
        seen = [0] * n
        for group in week:
            for golfer in group:
                seen[golfer] += 1
            for a, b in combinations(sorted(group), 2):
                meetings[(a, b)] = meetings.get((a, b), 0) + 1
        partition_errors += sum(abs(c - 1) for c in seen)
    repeated = sum(k - 1 for k in meetings.values() if k > 1)
    return repeated + partition_errors


def sci(log10_value):
    e = math.floor(log10_value)
    return f"{10 ** (log10_value - e):.2f}e{e}"


def log10_fact(x):
    return math.lgamma(x + 1) / math.log(10)


def landscape(g, p, w, samples=2000, seed=1):
    n = g * p
    partitions = log10_fact(n) - g * log10_fact(p) - log10_fact(g)   # log10 of n!/((p!)^g g!)

    print(f"Landscape for n={n} golfers, g={g} groups of p={p}, w={w} weeks\n")
    rows = [
        ("A  golfer per slot, domain 0..n-1         n^(n*w)", n * w * math.log10(n)),
        ("B  each week a permutation of golfers     (n!)^w", w * log10_fact(n)),
        ("C  each week a partition into groups      [n!/((p!)^g g!)]^w", w * partitions),
        ("D  C + week 1 fixed + weeks unordered     [..]^(w-1)/(w-1)!", (w - 1) * partitions - log10_fact(w - 1)),
    ]
    for name, val in rows:
        print(f"  {name:<62} = {sci(val)}")
    print(f"\n  partitions of {n} golfers into {g} groups of {p}: {sci(partitions)}")
    print(f"  pairs of golfers: C({n},2) = {n * (n - 1) // 2}; one week covers "
          f"g*C(p,2) = {g * p * (p - 1) // 2} pairs")
    print(f"  upper bound on weeks: floor((n-1)/(p-1)) = {(n - 1) // (p - 1)}")

    # how good are random schedules?
    rng = random.Random(seed)
    values = []
    for _ in range(samples):
        sched = []
        for _ in range(w):
            perm = list(range(n))
            rng.shuffle(perm)
            sched.append([perm[i * p:(i + 1) * p] for i in range(g)])
        values.append(objective(sched, n))
    values.sort()
    print(f"\n  Objective f over {samples} random schedules (representation C):")
    print(f"    min={values[0]}  median={values[len(values) // 2]}  "
          f"mean={sum(values) / len(values):.1f}  max={values[-1]}  "
          f"feasible (f=0): {values.count(0)}")


def print_schedule(schedule):
    g = len(schedule[0])
    width = max(len(",".join(map(str, grp))) for wk in schedule for grp in wk) + 1
    print(" " * 9 + " | ".join(f"{'Group ' + str(j + 1):<{width}}" for j in range(g)))
    for i, week in enumerate(schedule):
        cells = " | ".join(f"{','.join(map(str, sorted(grp))):<{width}}" for grp in week)
        print(f"Week {i + 1:<3} {cells}")


def run(g, p, w, strategy, time_limit, show=True):
    solver = SocialGolfersDFS(g, p, w, strategy, time_limit)
    found = solver.solve()
    status = {True: "SOLVED", False: "NO SOLUTION", None: "TIMEOUT"}[found]
    print(f"w={w:<3} {status:<12} nodes={solver.nodes:<12,} "
          f"backtracks={solver.backtracks:<12,} time={solver.elapsed:8.3f}s")
    if found and show:
        print()
        print_schedule(solver.schedule)
        print(f"\nObjective f(S) = {objective(solver.schedule, g * p)}  (0 = feasible)")
    return found, solver


def main():
    ap = argparse.ArgumentParser(description="Social Golfers Problem - DFS with backtracking")
    ap.add_argument("-g", type=int, default=8, help="number of groups (default 8)")
    ap.add_argument("-p", type=int, default=4, help="golfers per group (default 4)")
    ap.add_argument("-w", type=int, default=None, help="number of weeks (omit to search the maximum)")
    ap.add_argument("--max", action="store_true", help="increase w until DFS fails or times out")
    ap.add_argument("--strategy", choices=["freedom", "lex"], default="freedom",
                    help="child ordering of the DFS (default: freedom)")
    ap.add_argument("--time-limit", type=float, default=60, help="seconds per run (default 60)")
    ap.add_argument("--landscape", action="store_true", help="print search-space sizes and exit")
    args = ap.parse_args()

    g, p = args.g, args.p
    bound = (g * p - 1) // (p - 1)

    if args.landscape:
        landscape(g, p, args.w or bound)
        return

    print(f"Social Golfers: n={g * p} golfers, {g} groups of {p}, "
          f"strategy={args.strategy}, time limit={args.time_limit:g}s per run")
    print(f"Upper bound on weeks: floor((n-1)/(p-1)) = {bound}\n")

    if args.w is not None and not args.max:
        run(g, p, args.w, args.strategy, args.time_limit)
        return

    best = None
    for w in range(1, bound + 1):
        found, solver = run(g, p, w, args.strategy, args.time_limit, show=False)
        if not found:
            break
        best = solver
    if best:
        print(f"\nLargest schedule found: {best.w} weeks\n")
        print_schedule(best.schedule)
        print(f"\nObjective f(S) = {objective(best.schedule, g * p)}  (0 = feasible)")


if __name__ == "__main__":
    main()
