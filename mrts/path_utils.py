"""Filesystem-boundary helpers shared by MRTS command-line tools."""

from pathlib import Path


def _resolve_existing(path_value, label):
    try:
        return Path(path_value).expanduser().resolve(strict=True)
    except OSError as error:
        raise ValueError("{} does not resolve to an existing path".format(label)) from error


def existing_directory(path_value, label):
    """Return a canonical existing directory or raise a clear validation error."""
    path = _resolve_existing(path_value, label)
    if not path.is_dir():
        raise ValueError("{} must be an existing directory: {}".format(label, path))
    return path


def existing_file(path_value, label):
    """Return a canonical existing regular file or raise a clear validation error."""
    path = _resolve_existing(path_value, label)
    if not path.is_file():
        raise ValueError("{} must be an existing file: {}".format(label, path))
    return path


def path_within(directory, relative_path, label):
    """Resolve a child path and reject absolute, traversal, and symlink escapes."""
    root = existing_directory(directory, "{} directory".format(label))
    candidate = (root / relative_path).resolve(strict=False)
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise ValueError("{} must stay within {}".format(label, root)) from error
    if candidate == root:
        raise ValueError("{} must name a file or child path within {}".format(label, root))
    return candidate
