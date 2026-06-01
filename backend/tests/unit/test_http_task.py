import pytest
import requests

from src.worker.tasks.http_task import run_http_task

pytestmark = pytest.mark.unit


class FakeResponse:
    def __init__(self, ok=True, status_code=200, text="ok"):
        self.ok = ok
        self.status_code = status_code
        self.text = text


def test_run_http_task_success(monkeypatch):
    calls = []

    def fake_request(**kwargs):
        calls.append(kwargs)
        return FakeResponse(ok=True, status_code=200, text="done")

    monkeypatch.setattr(requests, "request", fake_request)

    result = run_http_task(
        {
            "method": "POST",
            "endpoint": "http://example.test/success",
            "headers": {"X-Test": "1"},
            "body": {"hello": "world"},
            "timeout": 7,
        },
        timeout_threshold=30,
    )

    assert result["status"] == "Success"
    assert result["error_message"] == ""
    assert "status_code=200" in result["log"]
    assert calls[0]["method"] == "POST"
    assert calls[0]["url"] == "http://example.test/success"
    assert calls[0]["headers"] == {"X-Test": "1"}
    assert calls[0]["json"] == {"hello": "world"}
    assert calls[0]["timeout"] == 7


def test_run_http_task_non_2xx_returns_failed(monkeypatch):
    monkeypatch.setattr(
        requests,
        "request",
        lambda **kwargs: FakeResponse(ok=False, status_code=500, text="boom"),
    )

    result = run_http_task(
        {"method": "GET", "endpoint": "http://example.test/fail"},
        timeout_threshold=30,
    )

    assert result["status"] == "Failed"
    assert result["error_message"] == "HTTP 500"
    assert "response_text=boom" in result["log"]


def test_run_http_task_missing_endpoint_returns_failed_without_request(monkeypatch):
    def fail_request(**kwargs):
        pytest.fail("request should not be called without endpoint")

    monkeypatch.setattr(requests, "request", fail_request)

    result = run_http_task({"method": "GET"}, timeout_threshold=30)

    assert result["status"] == "Failed"
    assert result["duration"] == 0
    assert result["error_message"] == "HTTP task endpoint is required"


def test_run_http_task_timeout_returns_timeout(monkeypatch):
    def fake_request(**kwargs):
        raise requests.Timeout("too slow")

    monkeypatch.setattr(requests, "request", fake_request)

    result = run_http_task(
        {"method": "GET", "endpoint": "http://example.test/timeout"},
        timeout_threshold=30,
    )

    assert result["status"] == "Timeout"
    assert result["error_message"] == "too slow"
    assert "error=timeout: too slow" in result["log"]


def test_run_http_task_request_exception_returns_failed(monkeypatch):
    def fake_request(**kwargs):
        raise requests.RequestException("network down")

    monkeypatch.setattr(requests, "request", fake_request)

    result = run_http_task(
        {"method": "GET", "endpoint": "http://example.test/error"},
        timeout_threshold=30,
    )

    assert result["status"] == "Failed"
    assert result["error_message"] == "network down"
    assert "error=request_exception: network down" in result["log"]


def test_run_http_task_empty_body_is_not_sent_as_json(monkeypatch):
    calls = []

    def fake_request(**kwargs):
        calls.append(kwargs)
        return FakeResponse()

    monkeypatch.setattr(requests, "request", fake_request)

    run_http_task(
        {
            "method": "POST",
            "endpoint": "http://example.test/no-body",
            "body": {},
        },
        timeout_threshold=30,
    )

    assert calls[0]["json"] is None
