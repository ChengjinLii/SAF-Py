import os
import shlex
import shutil
import subprocess
import sys

from ..._process import startup_environment, text_subprocess_kwargs


def _mrtrix_seed_extra_env(PS):
    """Forward the run-specific MRtrix seed to child processes."""

    seed = os.environ.get("MRTRIX_RNG_SEED") or getattr(PS, "random_seed", None)
    return {"MRTRIX_RNG_SEED": str(seed)} if seed is not None else None


def sys_exec(cmd, PS):
    """Run an external SAF command and stop immediately on failure."""

    extra_env = _mrtrix_seed_extra_env(PS)
    env = startup_environment(extra_env=extra_env)
    shell = True
    if sys.platform == "win32":
        # Backend paths use POSIX quoting, which cmd.exe does not understand.
        # Decode those quotes to argv, preserve the MRtrix PATH prefix in the
        # environment, and let the selected native/WSL executable handle argv.
        cmd = shlex.split(cmd) if isinstance(cmd, str) else list(cmd)
        if cmd and cmd[0].startswith("PATH="):
            prefix = cmd.pop(0)[len("PATH="):]
            if not prefix.endswith(":$PATH"):
                raise ValueError("Unsupported SAF PATH prefix on Windows; configure MRtrix bin directory")
            env["PATH"] = prefix[:-len(":$PATH")] + os.pathsep + env.get("PATH", "")
        if not cmd or any(token in {"&&", "||", "|", ";", ">", "<"} for token in cmd):
            raise ValueError("Windows SAF requires a single executable command, not shell operators")
        command = shutil.which(cmd[0], path=env.get("PATH", ""))
        if command:
            cmd[0] = command
        shell = False
    if getattr(PS, 'dgn', False):
        return subprocess.run(
            cmd,
            shell=shell,
            check=True,
            env=env,
        )
    return subprocess.run(
        cmd,
        shell=shell,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        **text_subprocess_kwargs(),
    )
