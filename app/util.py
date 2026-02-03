from pathlib import Path


def project_root(marker_files=("pyproject.toml", ".git")):
    current = Path(__file__).resolve()
    for parent in current.parents:
        if any((parent / m).exists() for m in marker_files):
            return parent
    return current.parent
