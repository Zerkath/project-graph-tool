#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "tree-sitter==0.24.0",
#   "tree-sitter-java==0.23.5",
#   "tree-sitter-scala==0.23.4",
#   "tree-sitter-kotlin==1.1.0",
#   "tree-sitter-python==0.23.6",
#   "networkx==3.4.2",
# ]
# ///
"""
Build a class graph from Java/Scala/Kotlin/Python source directories.

Graph hierarchy (JVM):    package → class → method
Graph hierarchy (Python): package → module → class → method
                          package → module → function
Cross-edges:              class/function --[instantiates]--> class

Usage:
    uvx visualize-project <dir_or_glob> [dir_or_glob ...]

Examples:
    uvx visualize-project ./src
    uvx visualize-project "*/src/main/scala"
    uvx visualize-project "projects/**/src/main/java" "projects/**/src/main/scala"
"""

import glob
import sys
from pathlib import Path

import networkx as nx
import tree_sitter_java
import tree_sitter_kotlin
import tree_sitter_python
import tree_sitter_scala
from tree_sitter import Language, Parser, Query

JAVA   = Language(tree_sitter_java.language())
SCALA  = Language(tree_sitter_scala.language())
KOTLIN = Language(tree_sitter_kotlin.language())
PYTHON = Language(tree_sitter_python.language())

LANG_MAP = {
    ".java":  JAVA,
    ".scala": SCALA,
    ".kt":    KOTLIN,
    ".py":    PYTHON,
}

SYNTAX_DIR = Path(__file__).parent / "syntax"

def load(lang: Language, lang_name: str, query_name: str) -> Query:
    path = SYNTAX_DIR / lang_name / f"{query_name}.scm"
    return lang.query(path.read_text())

QUERIES = {
    ".java": {
        "package": load(JAVA,   "java",   "package"),
        "classes": load(JAVA,   "java",   "classes"),
        "ctor":    load(JAVA,   "java",   "ctor"),
    },
    ".scala": {
        "package": load(SCALA,  "scala",  "package"),
        "classes": load(SCALA,  "scala",  "classes"),
        "ctor":    load(SCALA,  "scala",  "ctor"),
    },
    ".kt": {
        "package": load(KOTLIN, "kotlin", "package"),
        "classes": load(KOTLIN, "kotlin", "classes"),
        "ctor":    load(KOTLIN, "kotlin", "ctor"),
    },
    ".py": {
        "package":   load(PYTHON, "python", "package"),
        "classes":   load(PYTHON, "python", "classes"),
        "ctor":      load(PYTHON, "python", "ctor"),
        "functions": load(PYTHON, "python", "functions"),
    },
}

NODE_COLOUR = {
    "package":   (108,  92, 231),   # purple
    "module":    (162, 155, 254),   # lavender
    "class":     (  0, 184, 148),   # teal
    "interface": (  9, 132, 227),   # blue
    "method":    (253, 203, 110),   # amber
    "function":  (255, 159,  67),   # orange
}
DEFAULT_COLOUR = (178, 190, 195)    # grey

def node_colour(kind: str) -> tuple[int, int, int]:
    return NODE_COLOUR.get(kind, DEFAULT_COLOUR)

def resolve_dirs(patterns: list[str]) -> list[Path]:
    """Expand glob patterns and plain paths into a deduplicated list of dirs."""
    seen: set[Path] = set()
    dirs: list[Path] = []

    for pattern in patterns:
        matches = glob.glob(pattern, recursive=True)
        candidates = [Path(m) for m in matches] if matches else [Path(pattern)]

        for candidate in candidates:
            p = candidate.resolve()
            if not p.is_dir():
                print(f"WARNING: not a directory, skipping: {candidate}")
                continue
            if p in seen:
                continue
            # Skip if an ancestor is already in the list to avoid double-walking
            if any(p.is_relative_to(existing) for existing in seen):
                continue
            seen.add(p)
            dirs.append(p)

    if not dirs:
        print("ERROR: no valid directories found from the provided patterns")
        sys.exit(1)

    return dirs

def derive_python_package(path: Path) -> str | None:
    """Walk up parents while __init__.py exists and join their names."""
    parts: list[str] = []
    parent = path.parent
    while (parent / "__init__.py").exists():
        parts.append(parent.name)
        parent = parent.parent
    return ".".join(reversed(parts)) if parts else None

def python_module_name(path: Path) -> str:
    """`__init__.py` represents the package itself; otherwise use file stem."""
    return path.parent.name if path.name == "__init__.py" else path.stem

def extract_package(path: Path, root_node, queries: dict) -> str | None:
    if path.suffix == ".py":
        return derive_python_package(path)
    for _, captures in queries["package"].matches(root_node):
        for _, nodes in captures.items():
            for node in nodes:
                return node.text.decode()
    return None


def extract_symbols(path: Path):
    """Returns (package, classes, methods, functions, ctor_calls)."""
    lang    = LANG_MAP[path.suffix]
    queries = QUERIES[path.suffix]
    src     = path.read_bytes()
    root    = Parser(lang).parse(src).root_node

    package    = extract_package(path, root, queries)
    module_id  = str(path)
    classes    = {}
    methods    = []
    functions  = []

    for _, captures in queries["classes"].matches(root):
        class_nodes  = captures.get("class.name", [])
        method_nodes = captures.get("method.name", [])

        for class_node in class_nodes:
            if not class_node.text:
                continue
            class_name = class_node.text.decode()
            class_id   = f"{path}::{class_name}"
            classes[class_id] = {
                "name":    class_name,
                "file":    str(path),
                "line":    class_node.start_point[0] + 1,
                "lang":    path.suffix.lstrip("."),
                "package": package or "",
            }
            for method_node in method_nodes:
                if not method_node.text:
                    continue
                methods.append({
                    "name":     method_node.text.decode(),
                    "id":       f"{class_id}::{method_node.text.decode()}",
                    "class_id": class_id,
                    "file":     str(path),
                    "line":     method_node.start_point[0] + 1,
                    "lang":     path.suffix.lstrip("."),
                })

    if "functions" in queries:
        for _, captures in queries["functions"].matches(root):
            for func_node in captures.get("function.name", []):
                if not func_node.text:
                    continue
                func_name = func_node.text.decode()
                functions.append({
                    "name":      func_name,
                    "id":        f"{module_id}::{func_name}",
                    "module_id": module_id,
                    "file":      str(path),
                    "line":      func_node.start_point[0] + 1,
                    "lang":      path.suffix.lstrip("."),
                })

    # Containers for ctor attribution: classes + top-level functions, by start line.
    containers: list[tuple[int, str]] = [
        (cdata["line"], cid) for cid, cdata in classes.items()
    ] + [
        (fn["line"], fn["id"]) for fn in functions
    ]

    ctor_calls = []
    for _, captures in queries["ctor"].matches(root):
        for _, nodes in captures.items():
            for ctor_node in nodes:
                call_line = ctor_node.start_point[0] + 1
                best, best_start = None, -1
                for start_line, container_id in containers:
                    if start_line <= call_line and start_line > best_start:
                        best_start = start_line
                        best = container_id
                if best and ctor_node.text:
                    ctor_calls.append((best, ctor_node.text.decode()))

    return package, list(classes.values()), methods, functions, ctor_calls

def build_graph(dirs: list[Path]) -> nx.DiGraph:
    G = nx.DiGraph()
    all_ctor_calls = []

    # Pass 1 — nodes
    for root in dirs:
        for path in root.rglob("*"):
            if path.suffix not in LANG_MAP:
                continue

            package, classes, methods, functions, ctor_calls = extract_symbols(path)
            is_python = path.suffix == ".py"

            if package and not G.has_node(package):
                r, g, b = node_colour("package")
                G.add_node(package, kind="package", name=package, label=package, r=r, g=g, b=b)

            module_id = str(path)
            if is_python:
                mod_label = python_module_name(path)
                r, g, b   = node_colour("module")
                G.add_node(module_id, kind="module", name=mod_label, label=mod_label,
                           file=str(path), package=package or "",
                           lang=path.suffix.lstrip("."), r=r, g=g, b=b)
                if package:
                    G.add_edge(package, module_id, rel="contains")

            for cls in classes:
                class_id = f"{cls['file']}::{cls['name']}"
                r, g, b  = node_colour(cls.get("kind", "class"))
                G.add_node(class_id, kind="class", label=cls["name"], r=r, g=g, b=b, **cls)
                parent = module_id if is_python else package
                if parent:
                    G.add_edge(parent, class_id, rel="contains")

            for method in methods:
                r, g, b = node_colour("method")
                G.add_node(method["id"], kind="method", label=method["name"], r=r, g=g, b=b,
                           **{k: v for k, v in method.items() if k != "id"})
                G.add_edge(method["class_id"], method["id"], rel="has_method")

            for fn in functions:
                r, g, b = node_colour("function")
                G.add_node(fn["id"], kind="function", label=fn["name"], r=r, g=g, b=b,
                           **{k: v for k, v in fn.items() if k != "id"})
                G.add_edge(fn["module_id"], fn["id"], rel="has_function")

            all_ctor_calls.extend(ctor_calls)

    # Pass 2 — instantiation edges
    name_to_ids: dict[str, list[str]] = {}
    for node_id, data in G.nodes(data=True):
        if data.get("kind") == "class":
            name_to_ids.setdefault(data["name"], []).append(node_id)

    for caller_id, target_name in all_ctor_calls:
        if target_name not in name_to_ids or not G.has_node(caller_id):
            continue
        for target_id in name_to_ids[target_name]:
            if target_id != caller_id and not G.has_edge(caller_id, target_id):
                G.add_edge(caller_id, target_id, rel="instantiates")

    return G

def _print_class_subtree(G: nx.DiGraph, class_id: str, indent: str) -> None:
    cls = G.nodes[class_id]
    print(f"{indent}└─ [{cls['lang']:5}]  {cls['name']}  (line {cls['line']})")
    for method_id in G.successors(class_id):
        if G.edges[class_id, method_id].get("rel") == "has_method":
            m = G.nodes[method_id]
            print(f"{indent}     └─  {m['name']}  (line {m['line']})")

def main():
    patterns = sys.argv[1:] or ["."]
    dirs     = resolve_dirs(patterns)

    print(f"Scanning {len(dirs)} director{'y' if len(dirs) == 1 else 'ies'}:")
    for d in dirs:
        print(f"  {d}")

    G = build_graph(dirs)

    packages   = [(n, d) for n, d in G.nodes(data=True) if d.get("kind") == "package"]
    modules    = [(n, d) for n, d in G.nodes(data=True) if d.get("kind") == "module"]
    classes    = [(n, d) for n, d in G.nodes(data=True) if d.get("kind") == "class"]
    methods    = [(n, d) for n, d in G.nodes(data=True) if d.get("kind") == "method"]
    functions  = [(n, d) for n, d in G.nodes(data=True) if d.get("kind") == "function"]
    inst_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get("rel") == "instantiates"]

    print(f"\nFound {len(packages)} packages, {len(modules)} modules, {len(classes)} classes, "
          f"{len(methods)} methods, {len(functions)} functions, "
          f"{len(inst_edges)} instantiation edges:\n")

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

    gexf_out = Path("class_graph.gexf")
    nx.write_gexf(G, gexf_out)
    print(f"\nGraph written to {gexf_out}  (open in Gephi)")

    gml_out = Path("class_graph.graphml")
    nx.write_graphml(G, gml_out)
    print(f"Graph written to {gml_out}   (open in yEd)")

if __name__ == "__main__":
    main()
