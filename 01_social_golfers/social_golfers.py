"""
Social Golfers Problem - Depth First Search (DFS) with Backtracking
====================================================================

n = g * p golfers play golf once a week in g groups of p golfers.
Find a schedule for w weeks such that no two golfers play in the same
group more than once.  (Default instance: 32 golfers, 8 groups of 4.)

Representation
--------------
    schedule[week][group] = [golfer, golfer, ...]      (golfer in 0..n-1)

i.e. variable x(week, group, slot) with domain {0, ..., n-1}.

Constraints
-----------
    C1  every golfer plays exactly once per week            (partition)
    C2  two golfers play together at most once (socialisation constraint)

Search
------
The search tree is built by filling the schedule week by week and group
by group.  A node is a partial schedule, a child adds golfer(s) to the
next free position, a leaf at depth "all positions filled" is a goal.

DFS always expands the deepest node first.  Every time a child violates
C1 or C2 it is NOT generated (the branch is cut), and when a node has no
consistent child left the search BACKTRACKS to the previous decision and
tries the next value there.

Two branching strategies (both are DFS with backtracking, they differ
only in the ORDER in which children are tried):

  lex      textbook DFS: one golfer per level, children in increasing
           golfer order + symmetry breaking
              S1 golfers inside a group are increasing
              S2 groups ordered by their first golfer (first slot is forced)
              S3 week 1 fixed to {0..p-1}, {p..2p-1}, ...
              S4 weeks ordered by the 2nd golfer of group 1

  freedom  one PAIR of golfers per level; pairs are tried in order of
           minimal "freedom" (Triska & Musliu, 2012).  The freedom of a
           pair {a,b} is the number of golfers that neither a nor b has
           met yet - pairs that are about to run out of partners are
           scheduled first ("first fail").  S3 is also used.

Usage
-----
    python social_golfers.py                          # 8x4, max weeks (freedom)
    python social_golfers.py -w 9                     # exactly 9 weeks
    python social_golfers.py --strategy lex --max     # textbook DFS
    python social_golfers.py -g 5 -p 3 -w 7 --strategy lex --time-limit 300   # Kirkman's schoolgirls
    python social_golfers.py --landscape              # search-space sizes
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


class SearchTimeout(Exception):
    """Raised when the time limit of a run is reached."""


# ====================================================================== #
# DFS with backtracking
# ====================================================================== #
class SocialGolfersDFS:
    def __init__(self, g, p, w, strategy="freedom", time_limit=60):
        self.g, self.p, self.w = g, p, w
        self.n = g * p
        self.ALL = (1 << self.n) - 1
        self.strategy = strategy
        self.time_limit = time_limit

        self.schedule = [[[] for _ in range(g)] for _ in range(w)]
        self.met = [0] * self.n     # met[a]: bitmask of golfers a already played with
        self.used = [0] * w         # used[week]: bitmask of golfers placed that week

        # statistics
        self.nodes = 0              # generated (consistent) nodes
        self.backtracks = 0         # dead ends
        self.elapsed = 0.0
        self.start = None

        # positions = the levels of the search tree
        if strategy == "lex":
            sizes = [1] * p                         # one golfer per level
        else:
            sizes = [2] * (p // 2) + [1] * (p % 2)  # pairs (+ a single if p is odd)
        self.levels = []                            # (week, group, how many golfers)
        for wk in range(w):
            for gr in range(g):
                for k in sizes:
                    self.levels.append((wk, gr, k))

    # ---------------------------------------------------------------- #
    # apply / undo a decision
    # ---------------------------------------------------------------- #
    def _place(self, week, group, golfer):
        for m in self.schedule[week][group]:
            self.met[m] |= 1 << golfer
            self.met[golfer] |= 1 << m
        self.schedule[week][group].append(golfer)
        self.used[week] |= 1 << golfer

    def _remove(self, week, group):
        golfer = self.schedule[week][group].pop()
        for m in self.schedule[week][group]:
            self.met[m] &= ~(1 << golfer)
            self.met[golfer] &= ~(1 << m)
        self.used[week] &= ~(1 << golfer)

    def _compatible(self, week, group):
        """Golfers that may join (week, group): not used this week (C1) and
        not met with any current member of the group (C2)."""
        free = self.ALL & ~self.used[week]
        for m in self.schedule[week][group]:
            free &= ~self.met[m]
        return free

    # ---------------------------------------------------------------- #
    # children of a node (in the order DFS will try them)
    # ---------------------------------------------------------------- #
    def _children(self, week, group, k):
        free = self._compatible(week, group)

        if self.strategy == "lex":
            members = self.schedule[week][group]
            if not members:
                free &= -free                                   # S2
            else:
                free &= ~((1 << (members[-1] + 1)) - 1)         # S1
            if group == 0 and len(members) == 1 and week > 0:   # S4
                prev = self.schedule[week - 1][0][1]
                free &= ~((1 << (prev + 1)) - 1)
            while free:
                low = free & -free
                yield (low.bit_length() - 1,)
                free ^= low
            return

        # strategy "freedom"
        golfers = [i for i in range(self.n) if free >> i & 1]
        if k == 1:
            # single seat (odd p): golfers with fewer remaining partners first
            golfers.sort(key=lambda a: (popcount(self.ALL & ~self.met[a]), a))
            for a in golfers:
                yield (a,)
            return
        pairs = []
        for i, a in enumerate(golfers):
            for b in golfers[i + 1:]:
                if self.met[a] >> b & 1:
                    continue                                    # C2 for the pair
                both_unmet = self.ALL & ~self.met[a] & ~self.met[b] & ~(1 << a) & ~(1 << b)
                pairs.append((popcount(both_unmet), a, b))      # freedom of {a,b}
        pairs.sort()                                            # minimal freedom first
        for _, a, b in pairs:
            yield (a, b)

    # ---------------------------------------------------------------- #
    def _dfs(self, level):
        if level == len(self.levels):
            return True                                         # goal: schedule complete
        if self.time_limit and time.time() - self.start > self.time_limit:
            raise SearchTimeout

        week, group, k = self.levels[level]
        for child in self._children(week, group, k):
            self.nodes += 1
            for golfer in child:
                self._place(week, group, golfer)
            if self._dfs(level + 1):
                return True
            for _ in child:                                     # undo -> try next child
                self._remove(week, group)

        self.backtracks += 1                                    # dead end -> backtrack
        return False

    def solve(self):
        """True = solved, False = proven impossible (with this symmetry
        breaking), None = time limit reached."""
        self.start = time.time()
        level = 0
        if self.w > 0:                                          # S3: fix week 1
            for gr in range(self.g):
                for s in range(self.p):
                    self._place(0, gr, gr * self.p + s)
            while level < len(self.levels) and self.levels[level][0] == 0:
                level += 1
        try:
            found = self._dfs(level)
        except SearchTimeout:
            found = None
        self.elapsed = time.time() - self.start
        return found


# ====================================================================== #
# objective function
# ====================================================================== #
def objective(schedule, n):
    """f(S) = (number of repeated meetings) + (partition violations)

        repeated meetings   = sum over pairs {a,b} of max(0, m_ab - 1)
                              m_ab = number of weeks a and b share a group
        partition violation = golfer missing / appearing twice in a week

    f(S) = 0  <=>  S is a feasible schedule.  The optimisation version
    of the problem: maximise w such that min f(S) = 0.
    """
    meetings = {}
    partition_violations = 0
    for week in schedule:
        seen = [0] * n
        for group in week:
            for golfer in group:
                seen[golfer] += 1
            for a, b in combinations(sorted(group), 2):
                meetings[(a, b)] = meetings.get((a, b), 0) + 1
        partition_violations += sum(abs(c - 1) for c in seen)
    repeated = sum(k - 1 for k in meetings.values() if k > 1)
    return repeated + partition_violations


# ====================================================================== #
# landscape (size of the search space for different representations)
# ====================================================================== #
def sci(log10_value):
    exp = math.floor(log10_value)
    return f"{10 ** (log10_value - exp):.2f}e{exp}"


def landscape(g, p, w, samples=2000, seed=1):
    n = g * p
    lg = lambda x: math.lgamma(x + 1) / math.log(10)   # log10(x!)
    partitions = lg(n) - g * lg(p) - lg(g)              # log10 of n!/((p!)^g g!)

    print(f"Landscape for n={n} golfers, g={g} groups of p={p}, w={w} weeks\n")
    rows = [
        ("A  golfer per slot, domain 0..n-1         n^(n*w)",
         n * w * math.log10(n)),
        ("B  each week a permutation of golfers     (n!)^w",
         w * lg(n)),
        ("C  each week a partition into groups      [n!/((p!)^g g!)]^w",
         w * partitions),
        ("D  C + week 1 fixed + weeks unordered     [..]^(w-1)/(w-1)!",
         (w - 1) * partitions - lg(w - 1)),
    ]
    for name, val in rows:
        print(f"  {name:<62} = {sci(val)}")
    print(f"\n  partitions of {n} golfers into {g} groups of {p}: {sci(partitions)}")
    print(f"  pairs of golfers: C({n},2) = {n * (n - 1) // 2}; one week covers "
          f"g*C(p,2) = {g * p * (p - 1) // 2} pairs")
    print(f"  upper bound on weeks: floor((n-1)/(p-1)) = {(n - 1) // (p - 1)}")

    # sample the objective function over random points of representation C
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
    zeros = sum(1 for v in values if v == 0)
    print(f"\n  Objective f over {samples} random schedules (representation C):")
    print(f"    min={values[0]}  median={values[len(values) // 2]}  "
          f"mean={sum(values) / len(values):.1f}  max={values[-1]}  "
          f"feasible (f=0): {zeros}")


# ====================================================================== #
# output / CLI
# ====================================================================== #
def print_schedule(schedule):
    g = len(schedule[0])
    width = max(len(",".join(map(str, grp))) for wk in schedule for grp in wk) + 1
    print(" " * 9 + " | ".join(f"{'Group ' + str(j + 1):<{width}}" for j in range(g)))
    for i, week in enumerate(schedule):
        cells = " | ".join(f"{','.join(map(str, sorted(grp))):<{width}}" for grp in week)
        print(f"Week {i + 1:<3} {cells}")


def run_once(g, p, w, strategy, time_limit, show=True):
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
        run_once(g, p, args.w, args.strategy, args.time_limit)
        return

    best = None
    for w in range(1, bound + 1):
        found, solver = run_once(g, p, w, args.strategy, args.time_limit, show=False)
        if not found:
            break
        best = solver
    if best:
        print(f"\nLargest schedule found: {best.w} weeks\n")
        print_schedule(best.schedule)
        print(f"\nObjective f(S) = {objective(best.schedule, g * p)}  (0 = feasible)")


if __name__ == "__main__":
    main()
