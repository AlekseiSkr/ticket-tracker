import pytest
from django.core.exceptions import ImproperlyConfigured

from config.env import env_bool, env_int, env_list, require_env


def test_require_env_returns_value(monkeypatch):
    monkeypatch.setenv("SOME_VAR", "  value  ")
    assert require_env("SOME_VAR") == "value"


@pytest.mark.parametrize("raw", [None, "", "   "])
def test_require_env_fails_loudly_when_missing_or_blank(monkeypatch, raw):
    if raw is None:
        monkeypatch.delenv("SOME_VAR", raising=False)
    else:
        monkeypatch.setenv("SOME_VAR", raw)
    with pytest.raises(ImproperlyConfigured, match="SOME_VAR"):
        require_env("SOME_VAR")


def test_env_bool_rejects_garbage(monkeypatch):
    monkeypatch.setenv("FLAG", "maybe")
    with pytest.raises(ImproperlyConfigured):
        env_bool("FLAG")


def test_env_int_and_list(monkeypatch):
    monkeypatch.setenv("NUM", "42")
    monkeypatch.setenv("HOSTS", "a.example, b.example ,")
    assert env_int("NUM", 0) == 42
    assert env_list("HOSTS") == ["a.example", "b.example"]
