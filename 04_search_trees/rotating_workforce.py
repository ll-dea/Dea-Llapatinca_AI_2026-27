"""
Rotating Workforce Scheduling - DFS with backtracking, search tree.

A cyclic schedule for n employees is an n x 7 table. Every week an employee
moves to the next row, so reading the table row by row gives one cyclic
sequence of 7n days. Shifts: D = day, N = night, - = off.

Default instance (small enough to draw the whole tree):
    every day 1 x D and 1 x N, N->D forbidden,
    work blocks 2..4, off blocks 1..2, D blocks 1..3, N blocks 1..2

Cells are filled day by day (E1 Mon, E2 Mon, ..., E1 Tue, ...), values D, N, -.
A value that breaks a constraint is pruned, if all values fail DFS backtracks.

    python rotating_workforce.py
    python rotating_workforce.py --employees 4 --no-images
"""

import argparse
import sys
import time

from tree_tools import SearchTree, render

sys.setrecursionlimit(10000)

DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
OFF = "-"


class Instance:
    def __init__(self, employees=3):
        self.n = employees
        self.shifts = ["D", "N"]
        self.values = self.shifts + [OFF]
        self.req = {s: [1] * 7 for s in self.shifts}   # employees needed per shift, Mon..Sun
        self.forbidden = {("N", "D")}
        self.work_block = (2, 4)
        self.off_block = (1, 2)
        self.shift_block = {"D": (1, 3), "N": (1, 2)}
        self.length = 7 * employees

    def describe(self):
        return "\n".join([
            f"employees n = {self.n}  (cyclic schedule of {self.length} days)",
            "temporal requirements (Mon..Sun): " + ", ".join(f"{s}: {self.req[s]}" for s in self.shifts),
            "forbidden sequences: " + ", ".join(a + "->" + b for a, b in sorted(self.forbidden)),
            f"work blocks {self.work_block[0]}..{self.work_block[1]}, "
            f"days-off blocks {self.off_block[0]}..{self.off_block[1]}, shift blocks " +
            ", ".join(f"{s}: {lo}..{hi}" for s, (lo, hi) in self.shift_block.items()),
        ])


def runs(seq):
    """Blocks of equal known values in a cyclic list (None = not filled yet).
    Gives (value, length, closed), closed = both neighbours are known."""
    L = len(seq)
    if all(x is not None for x in seq) and len(set(seq)) == 1:
        yield seq[0], L, False
        return
    start = next(i for i in range(L) if seq[i] is None or seq[i] != seq[i - 1])
    i = 0
    while i < L:
        p = (start + i) % L
        if seq[p] is None:
            i += 1
            continue
        length = 1
        while i + length < L and seq[(p + length) % L] == seq[p]:
            length += 1
        left, right = seq[(p - 1) % L], seq[(p + length) % L]
        yield seq[p], length, left is not None and right is not None
        i += length


class Search:
    def __init__(self, inst, draw_limit=400, time_limit=60):
        self.inst = inst
        self.table = [[None] * 7 for _ in range(inst.n)]
        self.cells = [(e, d) for d in range(7) for e in range(inst.n)]   # day by day
        self.tree = SearchTree("Rotating Workforce Scheduling - DFS with backtracking  "
                               "(red = pruned, orange = backtracked, blue = solution path)")
        self.draw_limit = draw_limit
        self.time_limit = time_limit
        self.nodes = 0
        self.pruned = 0
        self.backtracks = 0
        self.goal_id = None
        self.start = None
        self.elapsed = 0

    def sequence(self):
        return [self.table[e][d] for e in range(self.inst.n) for d in range(7)]

    def violation(self, e, d):
        """Which constraint the value in (e, d) breaks, or None."""
        inst = self.inst
        v = self.table[e][d]

        # 1. how many of each shift on day d
        column = [self.table[i][d] for i in range(inst.n)]
        for s in inst.shifts:
            if column.count(s) > inst.req[s][d]:
                return f"too many {s} on {DAYS[d]}"
        offs_allowed = inst.n - sum(inst.req[s][d] for s in inst.shifts)
        if column.count(OFF) > offs_allowed:
            return f"too many off on {DAYS[d]}"

        # 2. forbidden sequences with the day before and after
        seq = self.sequence()
        L, k = len(seq), e * 7 + d
        prev, nxt = seq[(k - 1) % L], seq[(k + 1) % L]
        if prev is not None and (prev, v) in inst.forbidden:
            return f"{prev}->{v} forbidden"
        if nxt is not None and (v, nxt) in inst.forbidden:
            return f"{v}->{nxt} forbidden"

        # 3. block lengths (work/off first, then same shift)
        work_off = [None if x is None else ("off" if x == OFF else "work") for x in seq]
        bounds = {"work": inst.work_block, "off": inst.off_block}
        for value, length, closed in runs(work_off):
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

    def draw(self, label, parent, status):
        if parent is None or len(self.tree.nodes) >= self.draw_limit:
            return None
        return self.tree.add(label, parent, "", status)

    def dfs(self, idx, parent):
        if idx == len(self.cells):
            return True
        if time.time() - self.start > self.time_limit:
            raise TimeoutError
        e, d = self.cells[idx]
        for v in self.inst.values:
            self.nodes += 1
            self.table[e][d] = v
            reason = self.violation(e, d)
            label = f"E{e + 1} {DAYS[d]}={v}"
            if reason:
                self.pruned += 1
                self.draw(f"{label}\n{reason}", parent, "pruned")
                self.table[e][d] = None
                continue
            nid = self.draw(label, parent, "normal")
            if self.dfs(idx + 1, nid):
                if idx == len(self.cells) - 1:
                    self.goal_id = nid
                return True
            self.table[e][d] = None   # backtrack
        self.backtracks += 1
        return False

    def solve(self):
        self.start = time.time()
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
            for n in self.tree.nodes:
                if n["status"] == "normal":   # everything DFS came back from
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

    inst = Instance(employees=args.employees)
    print(inst.describe(), "\n")
    s = Search(inst, draw_limit=args.draw)
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
