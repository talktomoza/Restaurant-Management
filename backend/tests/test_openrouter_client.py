import pytest

from app.services.openrouter_client import call_openrouter_chat


class _FakeResponse:
    def __init__(self, status_code, json_body):
        self.status_code = status_code
        self._json_body = json_body

    def json(self):
        return self._json_body


class _FakeClient:
    def __init__(self, response):
        self._response = response
        self.last_request = None

    def post(self, url, headers=None, json=None, timeout=None):
        self.last_request = {"url": url, "headers": headers, "json": json}
        return self._response


def test_call_openrouter_chat_returns_content():
    fake = _FakeClient(_FakeResponse(200, {
        "choices": [{"message": {"content": '{"summary": "ok"}'}}]
    }))

    result = call_openrouter_chat("system prompt", "user data", http_client=fake)

    assert result == '{"summary": "ok"}'
    assert fake.last_request["headers"]["Authorization"].startswith("Bearer ")
    assert fake.last_request["json"]["messages"][0]["role"] == "system"


def test_call_openrouter_chat_raises_on_error_status():
    fake = _FakeClient(_FakeResponse(401, {"error": "unauthorized"}))

    with pytest.raises(RuntimeError):
        call_openrouter_chat("system prompt", "user data", http_client=fake)


def test_call_openrouter_chat_raises_on_malformed_body():
    fake = _FakeClient(_FakeResponse(200, {"unexpected": "shape"}))

    with pytest.raises(RuntimeError):
        call_openrouter_chat("system prompt", "user data", http_client=fake)
