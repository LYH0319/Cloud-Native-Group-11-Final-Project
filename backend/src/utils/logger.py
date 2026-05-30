import os
from pathlib import Path


LOG_ROOT = os.getenv("LOG_ROOT", "/app/logs")


def _log_root_path() -> Path:
    return Path(LOG_ROOT).expanduser().resolve()


def _resolve_log_path(log_path: str) -> Path:
    if not log_path:
        raise ValueError("log_path must not be empty")

    candidate = Path(log_path).expanduser()
    if not candidate.is_absolute():
        candidate = _log_root_path() / candidate

    return candidate.resolve()


def build_execution_log_path(execution_id: int | str) -> str:
    return str(_log_root_path() / "executions" / f"{execution_id}.log")


def validate_log_path(log_path: str) -> None:
    resolved_path = _resolve_log_path(log_path)
    log_root = _log_root_path()

    if resolved_path != log_root and log_root not in resolved_path.parents:
        raise ValueError("log_path must be inside LOG_ROOT")


def validate_log_size(log_size: int | None) -> None:
    if log_size is not None and log_size < 0:
        raise ValueError("log_size must not be negative")


def write_execution_log(execution_id: int | str, content: str) -> tuple[str, int]:
    log_path = build_execution_log_path(execution_id)
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as log_file:
        log_file.write(content)
    return log_path, path.stat().st_size


def read_execution_log(log_path: str) -> str:
    validate_log_path(log_path)
    with _resolve_log_path(log_path).open("r", encoding="utf-8", newline="") as log_file:
        return log_file.read()
