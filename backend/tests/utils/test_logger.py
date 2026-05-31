import pytest

from src.utils import logger as log_storage


def test_write_execution_log_creates_file_and_returns_size(tmp_path, monkeypatch):
    monkeypatch.setattr(log_storage, "LOG_ROOT", str(tmp_path))
    content = "hello\nlocal log\n"

    log_path, log_size = log_storage.write_execution_log(123, content)

    assert log_path == str(tmp_path / "executions" / "123.log")
    assert (tmp_path / "executions" / "123.log").read_text(encoding="utf-8") == content
    assert log_size == len(content.encode("utf-8"))


def test_read_execution_log_returns_content(tmp_path, monkeypatch):
    monkeypatch.setattr(log_storage, "LOG_ROOT", str(tmp_path))
    log_path, _ = log_storage.write_execution_log("abc", "stored content")

    assert log_storage.read_execution_log(log_path) == "stored content"


def test_read_execution_log_rejects_path_outside_log_root(tmp_path, monkeypatch):
    monkeypatch.setattr(log_storage, "LOG_ROOT", str(tmp_path / "logs"))
    outside = tmp_path / "outside.log"
    outside.write_text("secret", encoding="utf-8")

    with pytest.raises(ValueError):
        log_storage.read_execution_log(str(outside))
