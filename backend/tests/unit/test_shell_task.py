import pytest

from src.worker.tasks.shell_task import run_shell_task

pytestmark = pytest.mark.unit


def test_run_shell_task_returns_success_shape():
    result = run_shell_task({"command": "echo ok"}, timeout_threshold=30)

    assert result == {
        "status": "Success",
        "duration": 1.0,
        "error_message": "",
        "log": "MOCK SHELL SCRIPT SUCCESS",
    }
