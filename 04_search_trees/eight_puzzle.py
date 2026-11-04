"""
8-Puzzle search trees.

State = 9 numbers row by row, 0 is the blank. Moves = blank up/down/left/right.
Goal = 1 2 3 / 4 5 6 / 7 8 _

Builds the BFS tree (repeated states not expanded) and a depth limited DFS tree,
prints them and writes the pictures to img/.

    python eight_puzzle.py
    python eight_puzzle.py --start 023145786 --limit 4
"""

import argparse
from collections import deque

from tree_tools import SearchTree, render

GOAL = (1, 2, 3, 4, 5, 6, 7, 8, 0)
MOVES = [("Up", -3), ("Down", 3), ("Left", -1), ("Right", 1)]


def successors(state):
    b = state.index(0)
    r, c = divmod(b, 3)
    for name, delta in MOVES:
        if name == "Up" and r == 0 or name == "Down" and r == 2:
            continue
        if name == "Left" and c == 0 or name == "Right" and c == 2:
            continue
        s = list(state)
        s[b], s[b + delta] = s[b + delta], s[b]
        yield name, tuple(s)


def fmt(state):
    return "\n".join(" ".join(str(v) if v else "_" for v in state[i:i + 3]) for i in (0, 3, 6))


def complete_tree_counts(start, depth):
    """How many nodes the full tree has on every level (repeated states included)."""
    level, counts = [start], [1]
    for _ in range(depth):
        level = [s for st in level for _, s in successors(st)]
        counts.append(len(level))
    return counts


def bfs_tree(start, goal=GOAL, max_nodes=400):
    tree = SearchTree("8-Puzzle - BFS search tree (repeated states not expanded)")
    root = tree.add(fmt(start))
    if start == goal:
        tree.nodes[root]["status"] = "goal"
        return tree, root
    queue = deque([(root, start)])
    seen = {start}
    k = 0
    while queue and len(tree.nodes) < max_nodes:
        nid, state = queue.popleft()
        k += 1
        tree.set_order(nid, k)
        for action, child in successors(state):
            if child in seen:
                tree.add(fmt(child), nid, action, "repeated")
                continue
            cid = tree.add(fmt(child), nid, action)
            if child == goal:
                tree.nodes[cid]["status"] = "goal"
                tree.mark_path(cid)
                return tree, cid
            seen.add(child)
            queue.append((cid, child))
    return tree, None


def dfs_tree(start, limit, goal=GOAL):
    """Depth limited DFS, a state already on the current path is not visited again."""
    tree = SearchTree(f"8-Puzzle - DFS search tree (depth limit L = {limit})")
    counter = [0]

    def dls(state, nid, depth, path):
        counter[0] += 1
        tree.set_order(nid, counter[0])
        if state == goal:
            tree.nodes[nid]["status"] = "goal"
            return nid
        if depth == limit:
            tree.nodes[nid]["status"] = "cutoff"
            return None
        for action, child in successors(state):
            if child in path:
                tree.add(fmt(child), nid, action, "repeated")
                continue
            cid = tree.add(fmt(child), nid, action)
            found = dls(child, cid, depth + 1, path | {child})
            if found is not None:
                return found
        return None

    root = tree.add(fmt(start))
    goal_id = dls(start, root, 0, {start})
    if goal_id is not None:
        tree.mark_path(goal_id)
    return tree, goal_id


COLORS = {"normal": "#ffffff", "path": "#d7ecff", "goal": "#c8f0c8",
          "repeated": "#eeeeee", "cutoff": "#fff6d6", "pruned": "#fde2e2"}
BORDER = {"normal": "#555555", "path": "#1f6fb2", "goal": "#1d7a1d",
          "repeated": "#aaaaaa", "cutoff": "#b8860b", "pruned": "#c0392b"}


def html_grid(node):
    """Draws the board as a small table for Graphviz."""
    rows = [r.split() for r in node["label"].split("\n")]
    bg, border = COLORS[node["status"]], BORDER[node["status"]]
    font = "#888888" if node["status"] == "repeated" else "#000000"
    head = ""
    if node["order"] is not None or node["status"] in ("repeated", "cutoff", "goal"):
        txt = f"#{node['order']}" if node["order"] is not None else ""
        extra = {"repeated": "repeated", "cutoff": "cutoff", "goal": "GOAL"}.get(node["status"], "")
        head = (f'<TR><TD COLSPAN="3" BORDER="0"><FONT POINT-SIZE="9" COLOR="{border}">'
                f'{txt} {extra}</FONT></TD></TR>')
    cells = ""
    for r in rows:
        cells += "<TR>" + "".join(
            f'<TD WIDTH="16" HEIGHT="16" BGCOLOR="#cfcfcf"> </TD>' if v == "_" else
            f'<TD WIDTH="16" HEIGHT="16" BGCOLOR="{bg}"><FONT COLOR="{font}">{v}</FONT></TD>'
            for v in r) + "</TR>"
    return (f'<TABLE BORDER="2" CELLBORDER="1" CELLSPACING="0" CELLPADDING="2" '
            f'COLOR="{border}" BGCOLOR="{bg}">{head}{cells}</TABLE>')


def parse_state(text):
    digits = [int(ch) for ch in text if ch.isdigit()]
    if sorted(digits) != list(range(9)):
        raise SystemExit("the start state must contain the digits 0..8 once (0 = blank)")
    return tuple(digits)


def solvable(state):
    tiles = [t for t in state if t]
    inversions = sum(1 for i in range(8) for j in range(i + 1, 8) if tiles[i] > tiles[j])
    return inversions % 2 == 0


def main():
    ap = argparse.ArgumentParser(description="8-Puzzle search trees")
    ap.add_argument("--start", default="123046758", help="start state, row by row, 0 = blank")
    ap.add_argument("--limit", type=int, default=3, help="depth limit for DFS (default 3)")
    ap.add_argument("--max-nodes", type=int, default=3000,
                    help="stop BFS after this many generated nodes (default 3000)")
    ap.add_argument("--no-images", action="store_true", help="do not write img/ files")
    args = ap.parse_args()

    start = parse_state(args.start)
    print("Start state:\n" + fmt(start) + "\n\nGoal state:\n" + fmt(GOAL) + "\n")
    if not solvable(start):
        print("This start state is NOT solvable (odd number of inversions).")
        return

    counts = complete_tree_counts(start, 6)
    print("Complete search tree (every action, repeated states included):")
    for d, c in enumerate(counts):
        print(f"  depth {d}: {c:>5} nodes")
    print(f"  average branching factor at depth 1..6: "
          f"{(counts[-1] / counts[0]) ** (1 / (len(counts) - 1)):.2f}\n")

    bfs, bfs_goal = bfs_tree(start, max_nodes=args.max_nodes)
    print("BFS search tree  (#k = order of expansion)")
    print("\n".join(bfs.to_text()))
    print(f"\nBFS: {len(bfs.nodes)} nodes generated, {bfs.count('repeated')} repeated, "
          f"solution depth = {bfs.nodes[bfs_goal]['depth'] if bfs_goal is not None else '-'}")
    if bfs_goal is None:
        print(f"BFS stopped: node limit {args.max_nodes} reached (use --max-nodes)")
    print()

    dfs, dfs_goal = dfs_tree(start, args.limit)
    print(f"DFS search tree with depth limit {args.limit}  (#k = order of visit)")
    print("\n".join(dfs.to_text()))
    if dfs_goal is not None:
        print(f"\nDFS: {len(dfs.nodes)} nodes generated, goal found at depth {dfs.nodes[dfs_goal]['depth']}")
    else:
        print(f"\nDFS: {len(dfs.nodes)} nodes generated, no goal within the limit")

    if bfs_goal is not None:
        path, nid = [], bfs_goal
        while bfs.nodes[nid]["parent"] is not None:
            path.append(bfs.nodes[nid]["edge"])
            nid = bfs.nodes[nid]["parent"]
        print(f"\nSolution (moves of the blank): {' -> '.join(reversed(path))}")

    if not args.no_images:
        files = render(bfs.to_dot(html_label=html_grid), "img/8puzzle_bfs")
        files += render(dfs.to_dot(html_label=html_grid), "img/8puzzle_dfs")
        print("\nwritten:", ", ".join(files))


if __name__ == "__main__":
    main()
