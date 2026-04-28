"""Walk source dirs and assemble a NetworkX class graph."""

from pathlib import Path

import networkx as nx

from visualize_project.constants import LANG_MAP, node_colour
from visualize_project.graph.reader import extract_symbols, python_module_name


def _add_package(G: nx.DiGraph, package: str) -> None:
    if G.has_node(package):
        return
    r, g, b = node_colour("package")
    G.add_node(package, kind="package", name=package, label=package, r=r, g=g, b=b)


def _add_module(G: nx.DiGraph, path: Path, package: str | None) -> str:
    module_id = str(path)
    label     = python_module_name(path)
    r, g, b   = node_colour("module")
    G.add_node(module_id, kind="module", name=label, label=label,
               file=str(path), package=package or "",
               lang=path.suffix.lstrip("."), r=r, g=g, b=b)
    if package:
        G.add_edge(package, module_id, rel="contains")
    return module_id


def _add_class(G: nx.DiGraph, cls: dict, parent: str | None) -> None:
    class_id = f"{cls['file']}::{cls['name']}"
    r, g, b  = node_colour(cls.get("kind", "class"))
    G.add_node(class_id, kind="class", label=cls["name"], r=r, g=g, b=b, **cls)
    if parent:
        G.add_edge(parent, class_id, rel="contains")


def _add_method(G: nx.DiGraph, method: dict) -> None:
    r, g, b = node_colour("method")
    G.add_node(method["id"], kind="method", label=method["name"], r=r, g=g, b=b,
               **{k: v for k, v in method.items() if k != "id"})
    G.add_edge(method["class_id"], method["id"], rel="has_method")


def _add_function(G: nx.DiGraph, fn: dict) -> None:
    r, g, b = node_colour("function")
    G.add_node(fn["id"], kind="function", label=fn["name"], r=r, g=g, b=b,
               **{k: v for k, v in fn.items() if k != "id"})
    G.add_edge(fn["module_id"], fn["id"], rel="has_function")


def _ingest_file(G: nx.DiGraph, path: Path) -> list[tuple[str, str]]:
    package, classes, methods, functions, ctor_calls = extract_symbols(path)
    is_python = path.suffix == ".py"

    if package:
        _add_package(G, package)

    module_id = _add_module(G, path, package) if is_python else None
    class_parent = module_id if is_python else package

    for cls in classes:
        _add_class(G, cls, class_parent)
    for method in methods:
        _add_method(G, method)
    for fn in functions:
        _add_function(G, fn)

    return ctor_calls


def _iter_source_files(dirs: list[Path]):
    for root in dirs:
        for path in root.rglob("*"):
            if path.suffix in LANG_MAP:
                yield path


def _index_classes_by_name(G: nx.DiGraph) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for node_id, data in G.nodes(data=True):
        if data.get("kind") == "class":
            index.setdefault(data["name"], []).append(node_id)
    return index


def _add_instantiation_edges(G: nx.DiGraph, ctor_calls: list[tuple[str, str]]) -> None:
    name_to_ids = _index_classes_by_name(G)
    for caller_id, target_name in ctor_calls:
        if target_name not in name_to_ids or not G.has_node(caller_id):
            continue
        for target_id in name_to_ids[target_name]:
            if target_id != caller_id and not G.has_edge(caller_id, target_id):
                G.add_edge(caller_id, target_id, rel="instantiates")


def build_graph(dirs: list[Path]) -> nx.DiGraph:
    G = nx.DiGraph()
    all_ctor_calls: list[tuple[str, str]] = []

    for path in _iter_source_files(dirs):
        all_ctor_calls.extend(_ingest_file(G, path))

    _add_instantiation_edges(G, all_ctor_calls)
    return G
