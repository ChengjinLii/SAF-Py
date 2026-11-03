"""Small standalone replacements for the host application's process helpers."""

from __future__ import annotations

import os
import shutil
from pathlib import Path


def startup_environment(extra_env=None):
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    return env


def text_subprocess_kwargs():
    return {"text": True, "encoding": "utf-8", "errors": "replace"}


def resolve_external_command(command, bin_dir=None, *, require_executable=True):
    if bin_dir is None:
        return shutil.which(command)
    names = [command]
    if os.name == "nt":
        names.extend(command + ext.lower() for ext in os.environ.get("PATHEXT", ".EXE;.BAT;.CMD").split(";"))
    for name in names:
        candidate = Path(bin_dir) / name
        if candidate.is_file() and (not require_executable or os.access(candidate, os.X_OK)):
            return str(candidate)
    return None
