import time
from typing import Any

import requests


def run_http_task(payload: dict[str, Any], timeout_threshold: int):
    """Execute an HTTP task and return the worker result shape."""
    method = str(payload.get("method", "GET")).upper()
    endpoint = payload.get("endpoint")
    headers = payload.get("headers") or {}
    body = payload.get("body")
    timeout = payload.get("timeout") or timeout_threshold

    if not endpoint:
        return {
            "status": "Failed",
            "duration": 0,
            "error_message": "HTTP task endpoint is required",
            "log": "HTTP task failed before request: endpoint is required",
        }

    started = time.monotonic()
    try:
        response = requests.request(
            method=method,
            url=endpoint,
            headers=headers,
            json=body if body not in (None, {}) else None,
            timeout=timeout,
        )
        duration = time.monotonic() - started
        status = "Success" if response.ok else "Failed"
        error_message = "" if response.ok else f"HTTP {response.status_code}"
        log = "\n".join(
            [
                f"method={method}",
                f"endpoint={endpoint}",
                f"status_code={response.status_code}",
                f"duration={duration:.3f}",
                f"response_text={response.text}",
            ]
        )
        return {
            "status": status,
            "duration": duration,
            "error_message": error_message,
            "log": log,
        }
    except requests.Timeout as error:
        duration = time.monotonic() - started
        return {
            "status": "Timeout",
            "duration": duration,
            "error_message": str(error),
            "log": "\n".join(
                [
                    f"method={method}",
                    f"endpoint={endpoint}",
                    f"duration={duration:.3f}",
                    f"error=timeout: {error}",
                ]
            ),
        }
    except requests.RequestException as error:
        duration = time.monotonic() - started
        return {
            "status": "Failed",
            "duration": duration,
            "error_message": str(error),
            "log": "\n".join(
                [
                    f"method={method}",
                    f"endpoint={endpoint}",
                    f"duration={duration:.3f}",
                    f"error=request_exception: {error}",
                ]
            ),
        }
