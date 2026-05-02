"""Language parsers, tree-sitter queries, and node colour palette."""

from pathlib import Path

import tree_sitter_java
import tree_sitter_kotlin
import tree_sitter_python
import tree_sitter_scala
from tree_sitter import Language, Query

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


def _load(lang: Language, lang_name: str, query_name: str) -> Query:
    path = SYNTAX_DIR / lang_name / f"{query_name}.scm"
    return lang.query(path.read_text())


QUERIES = {
    ".java": {
        "package": _load(JAVA,   "java",   "package"),
        "classes": _load(JAVA,   "java",   "classes"),
        "ctor":    _load(JAVA,   "java",   "ctor"),
        "imports": _load(JAVA,   "java",   "imports"),
    },
    ".scala": {
        "package": _load(SCALA,  "scala",  "package"),
        "classes": _load(SCALA,  "scala",  "classes"),
        "ctor":    _load(SCALA,  "scala",  "ctor"),
        "imports": _load(SCALA,  "scala",  "imports"),
    },
    ".kt": {
        "package": _load(KOTLIN, "kotlin", "package"),
        "classes": _load(KOTLIN, "kotlin", "classes"),
        "ctor":    _load(KOTLIN, "kotlin", "ctor"),
        "imports": _load(KOTLIN, "kotlin", "imports"),
    },
    ".py": {
        "package":   _load(PYTHON, "python", "package"),
        "classes":   _load(PYTHON, "python", "classes"),
        "ctor":      _load(PYTHON, "python", "ctor"),
        "functions": _load(PYTHON, "python", "functions"),
        "imports":   _load(PYTHON, "python", "imports"),
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
