"""
Rotating Workforce Scheduling (RWS) - search tree of DFS with backtracking
==========================================================================

A cyclic schedule for n employees is an n x 7 table (rows = weeks,
columns = Mon..Sun).  In week 1 employee 1 works row 1, employee 2 row 2,
...; in week 2 every employee moves to the next row (the last row is
followed by the first one).  Reading the table row by row therefore gives
ONE cyclic sequence of 7n days that every employee works through.

Shifts:  D = day, N = night, '-' = day off

Constraints of the default instance (small, so the tree can be drawn):
    temporal requirements   every day: 1 employee on D and 1 on N
    forbidden sequence      N followed by D  (no day shift after a night)
    work blocks             2..4 consecutive working days
    days-off blocks         1..2 consecutive days off
    shift blocks            D: 1..3 in a row,  N: 1..2 in a row

Search tree:
    variables are filled DAY BY DAY (column by column): Mon of employee 1,
    Mon of employee 2, ..., then Tue, ...;  values are tried in the order
    D, N, -.  A child that violates a constraint is PRUNED (red), when all
    values of a cell fail the DFS BACKTRACKS to the previous cell.

Usage
-----
    python rotating_workforce.py                 # default instance
    python rotating_workforce.py --draw 80       # draw the first 80 nodes
    python rotating_workforce.py --employees 4 --no-images
"""

import argparse
import sys
import time

from tree_tools import SearchTree, render

sys.setrecursionlimit(10000)

DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
OFF = "-"


class RWSInstance:
    def __init__(self, employees=3, shifts=("D", "N"), requirements=None,
                 forbidden=(("N", "D"),), work_block=(2, 4), off_block=(1, 2),
                 shift_block=None):
        self.n = employees
        self.shifts = list(shifts)
        self.values = self.shifts + [OFF]
        # requirements[shift] = list of 7 numbers (Mon..Sun)
        self.req = requirements or {s: [1] * 7 for s in self.shifts}
        self.forbidden = set(forbidden)
        self.work_block = work_block
        self.off_block = off_block
        self.shift_block = shift_block or {"D": (1, 3), "N": (1, 2)}
        self.length = 7 * employees

    def describe(self):
        lines = [f"employees n = {self.n}  (cyclic schedule of {self.length} days)",
                 "temporal requirements (Mon..Sun): " +
                 ", ".join(f"{s}: {self.req[s]}" for s in self.shifts),
                 "forbidden sequences: " + ", ".join(a + "->" + b for a, b in sorted(self.forbidden)),
                 f"work blocks {self.work_block[0]}..{self.work_block[1]}, "
                 f"days-off blocks {self.off_block[0]}..{self.off_block[1]}, shift blocks " +
                 ", ".join(f"{s}: {lo}..{hi}" for s, (lo, hi) in self.shift_block.items())]
        return "\n".join(lines)


def runs(keys):
    """Maximal runs of equal, known values in a CYCLIC list (None = unknown).
    Yields (value, length, closed) - closed = both neighbours are known."""
    L = len(keys)
    if all(x is not None for x in keys) and len(set(keys)) == 1:
        yield keys[0], L, False                     # the whole cycle is one block
        return
    # start at a position where a new run begins
    start = next(i for i in range(L) if keys[i] is None or keys[i] != keys[i - 1])
    i = 0
    while i < L:
        p = (start + i) % L
        if keys[p] is None:
            i += 1
            continue
        length = 1
        while i + length < L and keys[(p + length) % L] == keys[p]:
            length += 1
        left, right = keys[(p - 1) % L], keys[(p + length) % L]
        yield keys[p], length, left is not None and right is not None
        i += length


class RWSSearch:
    def __init__(self, inst, draw_limit=400, time_limit=60):
        self.inst = inst
        self.table = [[None] * 7 for _ in range(inst.n)]
        # variable order: day by day
        self.cells = [(e, d) for d in range(7) for e in range(inst.n)]
        self.tree = SearchTree("Rotating Workforce Scheduling - DFS with backtracking  "
                               "(red = pruned, orange = backtracked, blue = solution path)")
        self.draw_limit = draw_limit
        self.nodes = 0
        self.pruned = 0
        self.backtracks = 0
        self.time_limit = time_limit

    # ---------------------------------------------------------------- #
    def sequence(self):
        """The cyclic sequence: row 1 Mon..Sun, row 2 Mon..Sun, ..."""
        return [self.table[e][d] for e in range(self.inst.n) for d in range(7)]

    def violation(self, e, d):
        """Reason why the value just written into (e, d) violates a
        constraint, or None.  Unassigned cells are treated as unknown."""
        inst, v = self.inst, self.table[e][d]

        # 1. temporal requirements of day d
        column = [self.table[i][d] for i in range(inst.n)]
        for s in inst.shifts:
            if column.count(s) > inst.req[s][d]:
                return f"too many {s} on {DAYS[d]}"
        offs_allowed = inst.n - sum(inst.req[s][d] for s in inst.shifts)
        if column.count(OFF) > offs_allowed:
            return f"too many off on {DAYS[d]}"

        # 2. forbidden sequences (with the previous and the next day)
        seq = self.sequence()
        L, k = len(seq), e * 7 + d
        prev, nxt = seq[(k - 1) % L], seq[(k + 1) % L]
        if prev is not None and (prev, v) in inst.forbidden:
            return f"{prev}->{v} forbidden"
        if nxt is not None and (v, nxt) in inst.forbidden:
            return f"{v}->{nxt} forbidden"

        # 3. block lengths
        work_or_off = [None if x is None else ("off" if x == OFF else "work") for x in seq]
        bounds = {"work": inst.work_block, "off": inst.off_block}
        for value, length, closed in runs(work_or_off):
            lo, hi = bounds[value]
            if length > hi:
                return f"{value} block > {hi}"
            if closed and length < lo:
                return f"{value} block < {lo}"
        for value, length, closed in runs(seq):
            if value == OFF:
                continue
            lo, hi = inst.shift_block[value]
            if length > hi:
                return f"{value} block > {hi}"
            if closed and length < lo:
                return f"{value} block < {lo}"
        return None

    # ---------------------------------------------------------------- #
    def _draw(self, label, parent, status):
        if parent is None or len(self.tree.nodes) >= self.draw_limit:
            return None
        return self.tree.add(label, parent, "", status)

    def dfs(self, idx, parent):
        """Fill cell number idx.  Returns True when the schedule is complete."""
        if idx == len(self.cells):
            return True                                     # goal test
        if time.time() - self.start > self.time_limit:
            raise TimeoutError
        e, d = self.cells[idx]
        for v in self.inst.values:                          # D, N, -
            self.nodes += 1
            self.table[e][d] = v
            reason = self.violation(e, d)
            label = f"E{e + 1} {DAYS[d]}={v}"
            if reason:                                      # prune this child
                self.pruned += 1
                self._draw(f"{label}\n{reason}", parent, "pruned")
                self.table[e][d] = None
                continue
            nid = self._draw(label, parent, "normal")
            if self.dfs(idx + 1, nid):
                if idx == len(self.cells) - 1:
                    self.goal_id = nid
                return True
            self.table[e][d] = None                         # undo
        self.backtracks += 1                                # dead end -> backtrack
        return False

    def solve(self):
        self.start = time.time()
        self.goal_id = None
        root = self.tree.add("empty schedule")
        try:
            found = self.dfs(0, root)
        except TimeoutError:
            found = None
        self.elapsed = time.time() - self.start
        if found and self.goal_id is not None:
            self.tree.nodes[self.goal_id]["status"] = "goal"
            self.tree.mark_path(self.goal_id)
            self.tree.nodes[0]["status"] = "path"
            for n in self.tree.nodes:                       # nodes DFS returned from
                if n["status"] == "normal":
                    n["status"] = "deadend"
        return found

    def table_text(self):
        out = ["Week/Row  " + "  ".join(DAYS)]
        for e in range(self.inst.n):
            out.append(f"   {e + 1:<6} " + "  ".join(f"{(x or '?'):>2}" for x in self.table[e]))
        return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="Rotating workforce scheduling - DFS search tree")
    ap.add_argument("--employees", type=int, default=3)
    ap.add_argument("--draw", type=int, default=400, help="maximum number of tree nodes to draw")
    ap.add_argument("--no-images", action="store_true")
    args = ap.parse_args()

    inst = RWSInstance(employees=args.employees)
    print(inst.describe(), "\n")
    s = RWSSearch(inst, draw_limit=args.draw)
    found = s.solve()
    print(f"nodes generated = {s.nodes}, pruned = {s.pruned}, backtracks = {s.backtracks}, "
          f"time = {s.elapsed:.3f}s")
    if not found:
        print("no schedule found" if found is False else "time limit reached")
    else:
        print("\n" + s.table_text())
        print("\ncyclic sequence:", " ".join(s.sequence()))
    print("\nFirst nodes of the search tree:")
    print("\n".join(s.tree.to_text()))
    if not args.no_images:
        print("\nwritten:", ", ".join(render(s.tree.to_dot(), "img/rws_dfs_tree")))


if __name__ == "__main__":
    main()
