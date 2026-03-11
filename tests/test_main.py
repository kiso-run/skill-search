"""End-to-end tests for main(): missing API key, unknown backend, max_results cap."""

import io
import json
import os
from unittest.mock import MagicMock, patch

import httpx
import pytest

import run


class TestMainMissingApiKey:
    def test_subprocess_exits_1(self, run_tool, make_input):
        result = run_tool(make_input("test query"), env={})
        assert result.returncode == 1

    def test_stdout_user_message(self, run_tool, make_input):
        result = run_tool(make_input("test query"), env={})
        assert "Search failed: API key not configured." in result.stdout

    def test_stderr_debug_message(self, run_tool, make_input):
        result = run_tool(make_input("test query"), env={})
        assert "KISO_SKILL_SEARCH_API_KEY is not set" in result.stderr

    def test_api_key_never_echoed(self, run_tool, make_input):
        """The key itself must never appear in stdout or stderr."""
        secret = "super-secret-key-12345"
        result = run_tool(
            make_input("test query"),
            env={"KISO_SKILL_SEARCH_API_KEY": secret},
        )
        assert secret not in result.stdout
        assert secret not in result.stderr


class TestMainUnknownBackend:
    _stdin = json.dumps({
        "args": {"query": "test"},
        "session": "s",
        "workspace": "/tmp",
        "session_secrets": {},
        "plan_outputs": [],
    })

    def test_exits_1(self, capsys):
        with patch("sys.stdin", io.StringIO(self._stdin)), \
             patch.dict(os.environ, {"KISO_SKILL_SEARCH_API_KEY": "fake-key"}), \
             patch("run.load_config", return_value={"backend": "bing"}):
            with pytest.raises(SystemExit) as exc_info:
                run.main()
        assert exc_info.value.code == 1

    def test_stdout_names_the_bad_backend(self, capsys):
        with patch("sys.stdin", io.StringIO(self._stdin)), \
             patch.dict(os.environ, {"KISO_SKILL_SEARCH_API_KEY": "fake-key"}), \
             patch("run.load_config", return_value={"backend": "bing"}):
            with pytest.raises(SystemExit):
                run.main()
        captured = capsys.readouterr()
        assert "unknown backend 'bing'" in captured.out


class TestMainMaxResultsCap:
    def _mock_brave_response(self, results=None):
        mock = MagicMock(spec=httpx.Response)
        mock.raise_for_status.return_value = None
        mock.json.return_value = {"web": {"results": results or []}}
        return mock

    def test_max_results_above_100_capped_to_100(self, capsys):
        stdin = json.dumps({
            "args": {"query": "test", "max_results": 200},
            "session": "s",
            "workspace": "/tmp",
            "session_secrets": {},
            "plan_outputs": [],
        })
        with patch("sys.stdin", io.StringIO(stdin)), \
             patch.dict(os.environ, {"KISO_SKILL_SEARCH_API_KEY": "fake-key"}), \
             patch("run.load_config", return_value={"backend": "brave"}), \
             patch("httpx.get", return_value=self._mock_brave_response()) as mock_get:
            run.main()
        assert mock_get.call_args[1]["params"]["count"] == 100

    def test_max_results_below_100_unchanged(self, capsys):
        stdin = json.dumps({
            "args": {"query": "test", "max_results": 7},
            "session": "s",
            "workspace": "/tmp",
            "session_secrets": {},
            "plan_outputs": [],
        })
        with patch("sys.stdin", io.StringIO(stdin)), \
             patch.dict(os.environ, {"KISO_SKILL_SEARCH_API_KEY": "fake-key"}), \
             patch("run.load_config", return_value={"backend": "brave"}), \
             patch("httpx.get", return_value=self._mock_brave_response()) as mock_get:
            run.main()
        assert mock_get.call_args[1]["params"]["count"] == 7

    def test_max_results_exactly_100_unchanged(self, capsys):
        stdin = json.dumps({
            "args": {"query": "test", "max_results": 100},
            "session": "s",
            "workspace": "/tmp",
            "session_secrets": {},
            "plan_outputs": [],
        })
        with patch("sys.stdin", io.StringIO(stdin)), \
             patch.dict(os.environ, {"KISO_SKILL_SEARCH_API_KEY": "fake-key"}), \
             patch("run.load_config", return_value={"backend": "brave"}), \
             patch("httpx.get", return_value=self._mock_brave_response()) as mock_get:
            run.main()
        assert mock_get.call_args[1]["params"]["count"] == 100
