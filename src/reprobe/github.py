from __future__ import annotations
import re
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path

from git import Repo
from git.exc import GitCommandError


def is_github_url(target: str) -> bool:
    return (
        target.startswith("https://github.com/")
        or target.startswith("http://github.com/")
        or target.startswith("git@github.com:")
    )


def repo_display_name(url: str) -> str:
    """Extract 'owner/repo' from a GitHub URL."""
    m = re.search(r"github\.com[/:](.+?/.+?)(?:\.git)?$", url)
    return m.group(1) if m else url


def _normalize(url: str) -> str:
    url = url.rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]
    return url


@contextmanager
def cloned(url: str):
    """Context manager: shallow-clone a GitHub repo, yield its path, then clean up."""
    url = _normalize(url)
    tmp = Path(tempfile.mkdtemp(prefix="reprobe_"))
    try:
        Repo.clone_from(url, tmp, depth=1, no_single_branch=True)
        yield tmp
    except GitCommandError as exc:
        raise RuntimeError(
            f"Could not clone {url!r}. "
            "Check that the repository exists and is public.\n"
            f"Detail: {exc}"
        ) from exc
    finally:
        shutil.rmtree(tmp, ignore_errors=True)