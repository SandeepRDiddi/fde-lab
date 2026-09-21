"""Runs a student's Python script in a lightweight, resource-limited
sandbox -- FDE-016's python_script task type needs actual code execution,
not just a read-only SQL query against an in-memory table (grading.py's
sql_query path). A script gets the scenario's dataset as an input JSON
file and must write a JSON output file; grading.py compares what it wrote
to a reference solution's output the same way.

Trust model, stated plainly: this bounds CPU time, memory, and open files,
and strips the parent process's environment (so a script can't read
secrets like API keys or DB credentials out of os.environ) -- it is a
training-lab-appropriate sandbox for trusted students, not a hardened
multi-tenant one. It does NOT provide network isolation: a script here
runs inside the same container and network namespace as the backend
itself, so it could still reach internal services (postgres, redis, minio,
persona-service, legacy-api) the way any other process in this container
can. Do not point this at untrusted/adversarial input without adding real
process isolation in front of it (a container-per-run, gVisor, Firecracker)
first -- that's a real, known gap, not an oversight.
"""
from __future__ import annotations

import json
import os
import resource
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

_TIMEOUT_SECONDS = 10.0
_MEMORY_LIMIT_BYTES = 256 * 1024 * 1024
_CPU_LIMIT_SECONDS = 10
_OPEN_FILES_LIMIT = 64


class CodeRunnerError(Exception):
    """The script failed to run, timed out, or its output couldn't be read
    as the JSON it's required to produce -- distinct from a scenario
    config problem (that's the caller's job to catch separately)."""


def _limit_resources() -> None:
    # Runs in the child process, right before exec, via subprocess's
    # preexec_fn -- caps what a runaway or hostile script can consume on
    # the host before it's ever allowed to run student code. Each limit is
    # applied independently and best-effort: RLIMIT_AS in particular is
    # unreliable on macOS (Darwin's virtual-memory accounting often refuses
    # a limit that Linux accepts fine) -- this backend always actually runs
    # in a Linux container (see infra/docker-compose.yml), so a limit that
    # can't be set on a contributor's local macOS dev machine shouldn't
    # crash the whole sandbox; it just means that one ceiling doesn't apply
    # outside the real deployment target.
    for limit, value in (
        (resource.RLIMIT_CPU, (_CPU_LIMIT_SECONDS, _CPU_LIMIT_SECONDS)),
        (resource.RLIMIT_AS, (_MEMORY_LIMIT_BYTES, _MEMORY_LIMIT_BYTES)),
        (resource.RLIMIT_NOFILE, (_OPEN_FILES_LIMIT, _OPEN_FILES_LIMIT)),
    ):
        try:
            resource.setrlimit(limit, value)
        except (ValueError, OSError):
            pass


def run_python_script(
    source: str,
    input_data: Any,
    *,
    input_filename: str = "input.json",
    output_filename: str = "output.json",
    timeout: float = _TIMEOUT_SECONDS,
) -> Any:
    """Writes `source` and `input_data` into a fresh temp directory, runs
    the script as a subprocess with that directory as its cwd, and returns
    the JSON it wrote to `output_filename`. Raises CodeRunnerError on a
    non-zero exit, a timeout, or a missing/unparseable output file."""
    with tempfile.TemporaryDirectory(prefix="fde-code-run-") as tmpdir:
        tmp_path = Path(tmpdir)
        (tmp_path / "solution.py").write_text(source)
        (tmp_path / input_filename).write_text(json.dumps(input_data))

        # Deliberately not os.environ -- a script here must not be able to
        # read this service's own secrets (DB credentials, the Groq API
        # key) out of its environment.
        env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "PYTHONDONTWRITEBYTECODE": "1"}

        try:
            result = subprocess.run(
                [sys.executable, "solution.py"],
                cwd=tmp_path,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout,
                preexec_fn=_limit_resources,
            )
        except subprocess.TimeoutExpired as exc:
            raise CodeRunnerError(f"Script timed out after {timeout:g}s") from exc

        if result.returncode != 0:
            stderr_tail = "\n".join(result.stderr.strip().splitlines()[-10:])
            raise CodeRunnerError(f"Script exited with code {result.returncode}:\n{stderr_tail}")

        output_path = tmp_path / output_filename
        if not output_path.exists():
            raise CodeRunnerError(f'Script did not write an output file named "{output_filename}"')

        try:
            return json.loads(output_path.read_text())
        except json.JSONDecodeError as exc:
            raise CodeRunnerError(f'Output file "{output_filename}" is not valid JSON: {exc}') from exc
