"""Analysis can read a different project without changing agent tracing."""

import sys
from types import SimpleNamespace

import pytest

from analysis.helpers import langfuse_io


def test_default_connection_remains_available(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in langfuse_io._ANALYSIS_KEYS:
        monkeypatch.delenv(key, raising=False)
    for key, value in zip(
        langfuse_io._DEFAULT_KEYS,
        ("app-public", "app-secret", "https://cloud.example"),
    ):
        monkeypatch.setenv(key, value)

    calls = []
    monkeypatch.setitem(
        sys.modules,
        "langfuse",
        SimpleNamespace(Langfuse=lambda **kwargs: calls.append(kwargs)),
    )

    assert langfuse_io.is_configured()
    langfuse_io._client()
    assert calls[0]["host"] == "https://cloud.example"


def test_analysis_connection_takes_precedence(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in zip(
        langfuse_io._DEFAULT_KEYS,
        ("app-public", "app-secret", "https://cloud.example"),
    ):
        monkeypatch.setenv(key, value)
    for key, value in zip(
        langfuse_io._ANALYSIS_KEYS,
        ("analysis-public", "analysis-secret", "http://localhost:3000"),
    ):
        monkeypatch.setenv(key, value)

    calls = []
    monkeypatch.setitem(
        sys.modules,
        "langfuse",
        SimpleNamespace(Langfuse=lambda **kwargs: calls.append(kwargs)),
    )

    assert langfuse_io.is_configured()
    langfuse_io._client()
    assert calls == [
        {
            "public_key": "analysis-public",
            "secret_key": "analysis-secret",
            "host": "http://localhost:3000",
        }
    ]


def test_partial_analysis_connection_does_not_use_app_project(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for key, value in zip(
        langfuse_io._DEFAULT_KEYS,
        ("app-public", "app-secret", "https://cloud.example"),
    ):
        monkeypatch.setenv(key, value)
    for key in langfuse_io._ANALYSIS_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv(langfuse_io._ANALYSIS_KEYS[0], "analysis-public")

    assert not langfuse_io.is_configured()
    with pytest.raises(langfuse_io.LangfuseNotConfigured):
        langfuse_io._client()
