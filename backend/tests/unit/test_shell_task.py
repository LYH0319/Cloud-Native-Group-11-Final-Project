import pytest
import sys

from src.worker.tasks.shell_task import run_shell_task

pytestmark = pytest.mark.unit


def test_run_shell_task_returns_success_shape():
    result = run_shell_task({"command": "echo ok"}, timeout_threshold=30)

    assert result["status"] == "Success"
    assert result["return_code"] == 0
    assert "ok" in result["log"]
    assert "stdout:" in result["log"]


def test_run_shell_task_returns_failed_on_non_zero_exit():
    command = f'"{sys.executable}" -c "import sys; print(\'bad\'); sys.exit(7)"'

    result = run_shell_task({"command": command}, timeout_threshold=30)

    assert result["status"] == "Failed"
    assert result["return_code"] == 7
    assert "Shell exited with code 7" in result["error_message"]
    assert "bad" in result["log"]


def test_run_shell_task_returns_timeout():
    command = f'"{sys.executable}" -c "import time; time.sleep(2)"'

    result = run_shell_task(
        {"command": command, "timeout_seconds": 0.2},
        timeout_threshold=30,
    )

    assert result["status"] == "Timeout"
    assert result["return_code"] is None
    assert "timed out" in result["error_message"]
