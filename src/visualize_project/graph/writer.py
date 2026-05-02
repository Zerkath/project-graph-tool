"""Walk source dirs and assemble a NetworkX class graph."""

from pathlib import Path

import networkx as nx

from visualize_project.constants import LANG_MAP, node_colour
from visualize_project.graph.reader import extract_symbols, python_module_name


def _add_package(G: nx.DiGraph, package: str, sep: str = ".") -> None:
    parts = package.split(sep)
    for i in range(len(parts)):
        full = sep.join(parts[: i + 1])
        if not G.has_node(full):
            r, g, b = node_colour("package")
            G.add_node(full, kind="package", name=full, label=full, r=r, g=g, b=b)
        if i > 0:
            parent = sep.join(parts[:i])
            if not G.has_edge(parent, full):
                G.add_edge(parent, full, rel="contains")


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


def _ingest_file(G: nx.DiGraph, path: Path):
    package, classes, methods, functions, ctor_calls, imports = extract_symbols(path)
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

    file_imports = [(package or "", path.suffix, rel_dots, target) for target, rel_dots in imports]
    return ctor_calls, file_imports


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


def _resolve_import_to_package(
    target: str, dots: int, src_package: str, packages: set[str], sep: str
) -> str | None:
    """Find the deepest known package matching the import.

    Python relative imports (``dots > 0``) are first rebased onto the
    source file's package — `from . import x` inside ``a.b`` becomes
    ``a.b.x``; ``..`` walks up further. JVM-style imports always carry
    the fully-qualified path (``a.b.c.Class``) — strip trailing
    segments until the prefix matches a known package.
    """
    if dots > 0:
        if not src_package:
            return None
        parts = src_package.split(sep)
        if dots > len(parts):
            return None
        base = parts[: len(parts) - (dots - 1)]
        target = sep.join(filter(None, [sep.join(base), target])).strip(sep)

    if not target:
        return None

    parts = target.split(sep)
    while parts:
        candidate = sep.join(parts)
        if candidate in packages and candidate != src_package:
            return candidate
        parts.pop()
    return None


def _add_import_edges(
    G: nx.DiGraph,
    file_imports: list[tuple[str, str, int, str]],
) -> None:
    packages = {n for n, d in G.nodes(data=True) if d.get("kind") == "package"}
    edge_weights: dict[tuple[str, str], int] = {}

    for src_package, suffix, dots, target in file_imports:
        if not src_package:
            continue
        sep = "." if suffix == ".py" else "."
        resolved = _resolve_import_to_package(target, dots, src_package, packages, sep)
        if not resolved:
            continue
        edge_weights[(src_package, resolved)] = edge_weights.get((src_package, resolved), 0) + 1

    for (src, dst), weight in edge_weights.items():
        if G.has_edge(src, dst):
            existing = G.edges[src, dst]
            if existing.get("rel") == "imports":
                existing["weight"] = existing.get("weight", 1) + weight
            else:
                # Don't clobber a `contains` edge — annotate it instead so the
                # import signal is still preserved in the serialized graph.
                existing["import_weight"] = existing.get("import_weight", 0) + weight
            continue
        G.add_edge(src, dst, rel="imports", weight=weight)


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
    all_imports: list[tuple[str, str, int, str]] = []

    for path in _iter_source_files(dirs):
        ctor_calls, file_imports = _ingest_file(G, path)
        all_ctor_calls.extend(ctor_calls)
        all_imports.extend(file_imports)

    _add_instantiation_edges(G, all_ctor_calls)
    _add_import_edges(G, all_imports)
    return G
