import subprocess
import time
from typing import Any


def _shell_config(payload: dict[str, Any]) -> dict[str, Any]:
    body = payload.get("body") if isinstance(payload.get("body"), dict) else {}
    return {**body, **payload}


def run_shell_task(payload: dict[str, Any], timeout_threshold: int):
    """Execute a shell command/script and return the worker result shape."""
    config = _shell_config(payload)
    command = config.get("command") or config.get("script")
    timeout = config.get("timeout_seconds") or config.get("timeout") or timeout_threshold

    if not command:
        return {
            "status": "Failed",
            "duration": 0,
            "error_message": "Shell task command or script is required",
            "return_code": None,
            "log": "Shell task failed before execution: command/script is required",
        }

    started = time.monotonic()
    process = None
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True,
        )
        stdout, stderr = process.communicate(timeout=timeout)
        duration = time.monotonic() - started
        return_code = process.returncode
        status = "Success" if return_code == 0 else "Failed"
        error_message = "" if return_code == 0 else f"Shell exited with code {return_code}"
        return {
            "status": status,
            "duration": duration,
            "error_message": error_message,
            "return_code": return_code,
            "log": "\n".join(
                [
                    f"command={command}",
                    f"exit_code={return_code}",
                    f"duration={duration:.3f}",
                    "stdout:",
                    stdout or "",
                    "stderr:",
                    stderr or "",
                ]
            ),
        }
    except subprocess.TimeoutExpired:
        if process is not None:
            process.kill()
            stdout, stderr = process.communicate()
        else:
            stdout, stderr = "", ""
        duration = time.monotonic() - started
        return {
            "status": "Timeout",
            "duration": duration,
            "error_message": f"Shell task timed out after {timeout} seconds",
            "return_code": None,
            "log": "\n".join(
                [
                    f"command={command}",
                    f"duration={duration:.3f}",
                    f"error=timeout after {timeout} seconds",
                    "stdout:",
                    stdout or "",
                    "stderr:",
                    stderr or "",
                ]
            ),
        }
    except Exception as error:
        duration = time.monotonic() - started
        return {
            "status": "Failed",
            "duration": duration,
            "error_message": str(error),
            "return_code": None,
            "log": "\n".join(
                [
                    f"command={command}",
                    f"duration={duration:.3f}",
                    f"error=shell_exception: {error}",
                ]
            ),
        }
