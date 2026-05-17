"""Parse a single source file into packages, classes, methods, functions, and ctor calls."""

from pathlib import Path

from tree_sitter import Parser

from visualize_project.constants import LANG_MAP, QUERIES


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
    lang = LANG_MAP[path.suffix]
    queries = QUERIES[path.suffix]
    src = path.read_bytes()
    root = Parser(lang).parse(src).root_node

    package = extract_package(path, root, queries)
    module_id = str(path)
    classes = {}
    methods = []
    functions = []

    for _, captures in queries["classes"].matches(root):
        class_nodes = captures.get("class.name", [])
        method_nodes = captures.get("method.name", [])

        for class_node in class_nodes:
            if not class_node.text:
                continue
            class_name = class_node.text.decode()
            class_id = f"{path}::{class_name}"
            classes[class_id] = {
                "name": class_name,
                "file": str(path),
                "line": class_node.start_point[0] + 1,
                "lang": path.suffix.lstrip("."),
                "package": package or "",
            }
            for method_node in method_nodes:
                if not method_node.text:
                    continue
                methods.append(
                    {
                        "name": method_node.text.decode(),
                        "id": f"{class_id}::{method_node.text.decode()}",
                        "class_id": class_id,
                        "file": str(path),
                        "line": method_node.start_point[0] + 1,
                        "lang": path.suffix.lstrip("."),
                    }
                )

    if "functions" in queries:
        for _, captures in queries["functions"].matches(root):
            for func_node in captures.get("function.name", []):
                if not func_node.text:
                    continue
                func_name = func_node.text.decode()
                functions.append(
                    {
                        "name": func_name,
                        "id": f"{module_id}::{func_name}",
                        "module_id": module_id,
                        "file": str(path),
                        "line": func_node.start_point[0] + 1,
                        "lang": path.suffix.lstrip("."),
                    }
                )

    # Containers for ctor attribution: classes + top-level functions, by start line.
    containers: list[tuple[int, str]] = [
        (cdata["line"], cid) for cid, cdata in classes.items()
    ] + [(fn["line"], fn["id"]) for fn in functions]

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
