"""
Missionaries and Cannibals - state space, BFS tree and DFS tree.

State = (M, C, B): missionaries and cannibals on the left bank, B = 1 if the
boat is on the left. Start (3,3,1), goal (0,0,0). The boat takes M, MM, C, CC
or MC. A state is illegal if cannibals outnumber missionaries on a bank.

    python missionaries_cannibals.py
    python missionaries_cannibals.py -m 4 -c 4 --capacity 3 --no-images
"""

import argparse
from collections import deque

from tree_tools import SearchTree, render


class Problem:
    def __init__(self, m=3, c=3, capacity=2):
        self.M = m
        self.C = c
        self.start = (m, c, 1)
        self.goal = (0, 0, 0)
        self.loads = [(i, j) for i in range(capacity + 1) for j in range(capacity + 1)
                      if 1 <= i + j <= capacity]
        # order the loads as M, MM, C, CC, MC
        self.loads.sort(key=lambda x: (0 if x[1] == 0 else 1 if x[0] == 0 else 2, x[0] + x[1]))

    def in_range(self, s):
        return 0 <= s[0] <= self.M and 0 <= s[1] <= self.C

    def legal(self, s):
        m, c, _ = s
        if not self.in_range(s):
            return False
        left_ok = m == 0 or m >= c
        right_ok = self.M - m == 0 or self.M - m >= self.C - c
        return left_ok and right_ok

    def children(self, s):
        """All moves, illegal results included (they are drawn as pruned nodes)."""
        m, c, b = s
        sign = -1 if b == 1 else 1
        for dm, dc in self.loads:
            t = (m + sign * dm, c + sign * dc, 1 - b)
            if self.in_range(t):
                who = "M" * dm + "C" * dc
                yield (f"{who} ->" if b == 1 else f"<- {who}"), t

    def label(self, s):
        m, c, b = s
        left = "M" * m + "C" * c or "-"
        right = "M" * (self.M - m) + "C" * (self.C - c) or "-"
        boat_l, boat_r = ("[B]", "   ") if b == 1 else ("   ", "[B]")
        return f"({m},{c},{b})\n{left} {boat_l}~~{boat_r} {right}"


def state_space(p):
    """All legal states reachable from the start, plus the moves between them."""
    states, edges = {p.start}, {}
    queue = deque([p.start])
    while queue:
        s = queue.popleft()
        for act, t in p.children(s):
            if p.legal(t):
                edges[tuple(sorted([s, t]))] = act.replace("->", "").replace("<-", "").strip()
                if t not in states:
                    states.add(t)
                    queue.append(t)
    return states, edges


def search_tree(p, strategy):
    """BFS (queue) or DFS (stack), states visited before are not expanded again."""
    tree = SearchTree(f"Missionaries & Cannibals - {strategy.upper()} search tree "
                      f"(red = illegal, grey = repeated)")
    root = tree.add(p.label(p.start), data=p.start)
    frontier = deque([(root, p.start)])
    visited = {p.start}
    k = 0
    while frontier:
        nid, s = frontier.popleft() if strategy == "bfs" else frontier.pop()
        k += 1
        tree.set_order(nid, k)
        if s == p.goal:
            tree.nodes[nid]["status"] = "goal"
            tree.mark_path(nid)
            return tree, nid
        new = []
        for act, t in p.children(s):
            if not p.legal(t):
                tree.add(p.label(t), nid, act, "pruned", data=t)
            elif t in visited:
                tree.add(p.label(t), nid, act, "repeated", data=t)
            else:
                visited.add(t)
                new.append((tree.add(p.label(t), nid, act, data=t), t))
        # for DFS push in reverse so the first move is tried first
        frontier.extend(new if strategy == "bfs" else reversed(new))
    return tree, None


def solution_path(tree, goal_id):
    path, nid = [], goal_id
    while nid is not None:
        n = tree.nodes[nid]
        path.append((n["edge"], n["data"]))
        nid = n["parent"]
    return list(reversed(path))


def state_space_dot(p, states, edges, solution):
    lines = [
        "graph G {",
        '  graph [labelloc="t", fontsize=20, fontname="Helvetica", '
        'label="Missionaries & Cannibals - complete state space (legal states)", '
        'rankdir=LR, nodesep=0.25, ranksep=0.6];',
        '  node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, fillcolor="#ffffff"];',
        '  edge [fontname="Helvetica", fontsize=9, color="#888888"];',
    ]
    for s in sorted(states, key=lambda s: (-(s[0] + s[1]), -s[2], -s[0])):
        style = ""
        if s == p.start:
            style = ', fillcolor="#d7ecff", color="#1f6fb2", penwidth=2'
        elif s == p.goal:
            style = ', fillcolor="#c8f0c8", color="#1d7a1d", penwidth=2'
        elif s in solution:
            style = ', color="#1f6fb2", penwidth=2'
        lab = p.label(s).replace("\n", "\\n")
        lines.append(f'  "{s}" [label="{lab}"{style}];')
    sol_pairs = {tuple(sorted(pair)) for pair in zip(solution, solution[1:])}
    for (a, b), load in sorted(edges.items()):
        bold = ', color="#1f6fb2", penwidth=2.5' if (a, b) in sol_pairs else ""
        lines.append(f'  "{a}" -- "{b}" [label="{load}"{bold}];')
    lines.append("}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Missionaries and Cannibals search trees")
    ap.add_argument("-m", type=int, default=3, help="missionaries (default 3)")
    ap.add_argument("-c", type=int, default=3, help="cannibals (default 3)")
    ap.add_argument("--capacity", type=int, default=2, help="boat capacity (default 2)")
    ap.add_argument("--no-images", action="store_true")
    args = ap.parse_args()

    p = Problem(args.m, args.c, args.capacity)
    states, edges = state_space(p)
    total = (p.M + 1) * (p.C + 1) * 2
    legal = sum(1 for m in range(p.M + 1) for c in range(p.C + 1) for b in (0, 1) if p.legal((m, c, b)))
    print(f"State space: (M+1)(C+1)*2 = {total} states, {legal} legal, "
          f"{len(states)} legal and reachable from {p.start}, {len(edges)} edges\n")

    results = {}
    for strategy in ("bfs", "dfs"):
        tree, goal = search_tree(p, strategy)
        results[strategy] = (tree, goal)
        print(f"{strategy.upper()} search tree  (#k = order of expansion)")
        print("\n".join(tree.to_text()))
        expanded = sum(1 for n in tree.nodes if n["order"] is not None)
        print(f"\n{strategy.upper()}: generated {len(tree.nodes)} nodes, expanded {expanded}, "
              f"illegal {tree.count('pruned')}, repeated {tree.count('repeated')}")
        if goal is None:
            print("no solution\n")
            continue
        path = solution_path(tree, goal)
        print(f"solution with {len(path) - 1} crossings:")
        for act, st in path:
            print(f"   {act:>8}  {p.label(st).replace(chr(10), '   ')}")
        print()

    if not args.no_images and results["bfs"][1] is not None:
        bfs_tree, goal = results["bfs"]
        solution = [st for _, st in solution_path(bfs_tree, goal)]
        files = render(state_space_dot(p, states, edges, solution), "img/mc_state_space")
        for strategy in ("bfs", "dfs"):
            files += render(results[strategy][0].to_dot(), f"img/mc_{strategy}_tree")
        print("written:", ", ".join(files))


if __name__ == "__main__":
    main()
