"""Resolve user-supplied glob patterns and paths into source directories."""

import glob
import sys
from pathlib import Path


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
