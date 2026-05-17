"""Pretty-print the graph to stdout and write a graphology JSON file."""

import json
from pathlib import Path

import networkx as nx


def _print_class_subtree(G: nx.DiGraph, class_id: str, indent: str) -> None:
    cls = G.nodes[class_id]
    print(f"{indent}└─ [{cls['lang']:5}]  {cls['name']}  (line {cls['line']})")
    for method_id in G.successors(class_id):
        if G.edges[class_id, method_id].get("rel") == "has_method":
            m = G.nodes[method_id]
            print(f"{indent}     └─  {m['name']}  (line {m['line']})")


def print_summary(G: nx.DiGraph) -> None:
    packages = [(n, d) for n, d in G.nodes(data=True) if d.get("kind") == "package"]
    modules = [(n, d) for n, d in G.nodes(data=True) if d.get("kind") == "module"]
    classes = [(n, d) for n, d in G.nodes(data=True) if d.get("kind") == "class"]
    methods = [(n, d) for n, d in G.nodes(data=True) if d.get("kind") == "method"]
    functions = [(n, d) for n, d in G.nodes(data=True) if d.get("kind") == "function"]
    inst_edges = [
        (u, v) for u, v, d in G.edges(data=True) if d.get("rel") == "instantiates"
    ]

    print(
        f"\nFound {len(packages)} packages, {len(modules)} modules, {len(classes)} classes, "
        f"{len(methods)} methods, {len(functions)} functions, "
        f"{len(inst_edges)} instantiation edges:\n"
    )

    for pkg_id, pkg in sorted(packages, key=lambda x: x[1]["name"]):
        print(f"  pkg  {pkg['name']}")
        for child_id in G.successors(pkg_id):
            child = G.nodes[child_id]
            if child.get("kind") == "module":
                print(f"    mod  {child['name']}  ({child['file']})")
                for sub_id in G.successors(child_id):
                    sub = G.nodes[sub_id]
                    if sub.get("kind") == "class":
                        _print_class_subtree(G, sub_id, indent="      ")
                    elif sub.get("kind") == "function":
                        print(f"      └─ fn  {sub['name']}  (line {sub['line']})")
            elif child.get("kind") == "class":
                _print_class_subtree(G, child_id, indent="    ")

    if inst_edges:
        print("\n  Instantiation edges:")
        for u, v in sorted(inst_edges, key=lambda e: G.nodes[e[0]].get("name", "")):
            print(f"    {G.nodes[u]['name']}  →  {G.nodes[v]['name']}")

    orphans = [(n, d) for n, d in classes if not d.get("package")]
    if orphans:
        print(f"\n  (no package)  {len(orphans)} classes")
        for n, d in orphans:
            print(f"    └─ {d['name']}  ({d['file']}:{d['line']})")


def _to_graphology(G: nx.DiGraph) -> dict:
    return {
        "options": {
            "type": "directed",
            "multi": False,
            "allowSelfLoops": True,
        },
        "attributes": {},
        "nodes": [
            {"key": str(n), "attributes": dict(data)} for n, data in G.nodes(data=True)
        ],
        "edges": [
            {"source": str(u), "target": str(v), "attributes": dict(data)}
            for u, v, data in G.edges(data=True)
        ],
    }


_TEMPLATE_PATH = Path(__file__).parent / "notebook_template.py"


def _to_notebook() -> dict:
    code = _TEMPLATE_PATH.read_text(encoding="utf-8")
    return {
        "cells": [
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": code.splitlines(keepends=True),
            },
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def write_graph_files(G: nx.DiGraph) -> None:
    out = Path("class_graph.json")
    with out.open("w", encoding="utf-8") as f:
        json.dump(_to_graphology(G), f, ensure_ascii=False, indent=2)
    print(f"\nGraph written to {out}")

    nb = Path("class_graph.ipynb")
    with nb.open("w", encoding="utf-8") as f:
        json.dump(_to_notebook(), f, ensure_ascii=False, indent=1)
    print(f"Notebook written to {nb}")
    print(
        f"\nTo view, run:\n  uvx --with networkx --with ipysigma --with jupyter voila {nb}"
    )
