"""
Small helper used by the three search-tree scripts.

SearchTree records every node that a search algorithm generates and can
export the tree as
    * indented text (printed to the console), and
    * Graphviz DOT (rendered to PNG/SVG when the `dot` program is installed).

Node status
    normal    expanded / generated node
    goal      goal node
    path      node on the solution path
    pruned    child that violates a constraint (dead end -> backtracking)
    repeated  child whose state was already visited (not expanded again)
    cutoff    node at the depth limit (depth-limited search)
    deadend   consistent node whose subtree has no solution (DFS backtracked)
"""

import os
import shutil
import subprocess

STYLE = {
    "normal":   'style="filled", fillcolor="#ffffff", color="#555555"',
    "path":     'style="filled", fillcolor="#d7ecff", color="#1f6fb2", penwidth=2',
    "goal":     'style="filled", fillcolor="#c8f0c8", color="#1d7a1d", penwidth=2.5',
    "pruned":   'style="filled,dashed", fillcolor="#fde2e2", color="#c0392b", fontcolor="#c0392b"',
    "repeated": 'style="filled,dashed", fillcolor="#eeeeee", color="#999999", fontcolor="#777777"',
    "cutoff":   'style="filled,dotted", fillcolor="#fff6d6", color="#b8860b"',
    "deadend":  'style="filled", fillcolor="#ffe9cc", color="#d68910"',
}


class SearchTree:
    def __init__(self, title=""):
        self.title = title
        self.nodes = []        # dicts: id, parent, label, edge, status, order, depth

    def add(self, label, parent=None, edge="", status="normal", data=None):
        depth = 0 if parent is None else self.nodes[parent]["depth"] + 1
        node = {"id": len(self.nodes), "parent": parent, "label": label, "data": data,
                "edge": edge, "status": status, "order": None, "depth": depth}
        self.nodes.append(node)
        return node["id"]

    def set_order(self, node_id, k):
        self.nodes[node_id]["order"] = k

    def mark_path(self, goal_id):
        nid = self.nodes[goal_id]["parent"]
        while nid is not None:
            if self.nodes[nid]["status"] == "normal":
                self.nodes[nid]["status"] = "path"
            nid = self.nodes[nid]["parent"]

    def children(self, node_id):
        return [n for n in self.nodes if n["parent"] == node_id]

    def count(self, status=None):
        return sum(1 for n in self.nodes if status is None or n["status"] == status)

    # ---------------------------------------------------------------- #
    def to_text(self, node_id=0, indent="", last=True, out=None):
        out = [] if out is None else out
        n = self.nodes[node_id]
        tag = {"goal": "  <== GOAL", "pruned": "  [X pruned]", "deadend": "  [backtrack]",
               "repeated": "  [repeated]", "cutoff": "  [cutoff]"}.get(n["status"], "")
        order = f"#{n['order']} " if n["order"] is not None else ""
        label = n["label"].replace("\n", " ")
        edge = f"[{n['edge']}] " if n["edge"] else ""
        branch = "" if n["parent"] is None else ("`-- " if last else "|-- ")
        out.append(f"{indent}{branch}{edge}{order}{label}{tag}")
        kids = self.children(node_id)
        for i, k in enumerate(kids):
            ext = "" if n["parent"] is None else ("    " if last else "|   ")
            self.to_text(k["id"], indent + ext, i == len(kids) - 1, out)
        return out

    def to_dot(self, html_label=None, rankdir="TB", font="Helvetica"):
        """html_label: optional function node -> Graphviz HTML label."""
        lines = [
            "digraph G {",
            f'  graph [rankdir={rankdir}, labelloc="t", fontsize=20, fontname="{font}", '
            f'label="{self.title}", nodesep=0.15, ranksep=0.45];',
            f'  node [shape=box, fontname="{font}", fontsize=11, margin="0.06,0.03"];',
            f'  edge [fontname="{font}", fontsize=10, color="#666666", arrowsize=0.6];',
        ]
        for n in self.nodes:
            order = f"#{n['order']}" if n["order"] is not None else ""
            if html_label:
                lines.append(f'  n{n["id"]} [label=<{html_label(n)}>, shape=plain];')
            else:
                text = n["label"].replace('"', '\\"').replace("\n", "\\n")
                if order:
                    text = f"{order}\\n{text}"
                lines.append(f'  n{n["id"]} [label="{text}", {STYLE[n["status"]]}];')
        for n in self.nodes:
            if n["parent"] is not None:
                bold = ', penwidth=2.2, color="#1f6fb2"' if n["status"] in ("path", "goal") else ""
                lab = n["edge"].replace('"', '\\"')
                lines.append(f'  n{n["parent"]} -> n{n["id"]} [label=" {lab}"{bold}];')
        lines.append("}")
        return "\n".join(lines)


def render(dot_source, path_without_ext, formats=("png", "svg")):
    """Write <path>.dot and, if Graphviz is installed, <path>.png/.svg."""
    os.makedirs(os.path.dirname(path_without_ext) or ".", exist_ok=True)
    with open(path_without_ext + ".dot", "w", encoding="utf-8") as fh:
        fh.write(dot_source)
    written = [path_without_ext + ".dot"]
    if shutil.which("dot"):
        for fmt in formats:
            out = f"{path_without_ext}.{fmt}"
            subprocess.run(["dot", f"-T{fmt}", "-Gdpi=110", path_without_ext + ".dot", "-o", out],
                           check=True)
            written.append(out)
    return written
