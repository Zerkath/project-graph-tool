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

import sys

from visualize_project.discovery import resolve_dirs
from visualize_project.graph import build_graph
from visualize_project.report import print_summary, write_graph_files


def main() -> None:
    patterns = sys.argv[1:] or ["."]
    dirs = resolve_dirs(patterns)

    print(f"Scanning {len(dirs)} director{'y' if len(dirs) == 1 else 'ies'}:")
    for d in dirs:
        print(f"  {d}")

    G = build_graph(dirs)
    print_summary(G)
    write_graph_files(G)


if __name__ == "__main__":
    main()
