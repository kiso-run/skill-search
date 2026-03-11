import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent


@pytest.fixture
def make_input():
    def _make(query="test query", max_results=5, language=None, country=None):
        args = {"query": query, "max_results": max_results}
        if language:
            args["language"] = language
        if country:
            args["country"] = country
        return {
            "args": args,
            "session": "test-session",
            "workspace": "/tmp/test-workspace",
            "session_secrets": {},
            "plan_outputs": [],
        }
    return _make


@pytest.fixture
def run_tool():
    """Run run.py as a subprocess with controlled stdin and env."""
    def _run(input_data, env=None):
        process_env = {"PATH": os.environ.get("PATH", "")}
        if env:
            process_env.update(env)
        return subprocess.run(
            [sys.executable, str(ROOT / "run.py")],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
            env=process_env,
            timeout=10,
        )
    return _run


@pytest.fixture
def brave_response_ok():
    return {
        "web": {
            "results": [
                {
                    "title": "Python Async Patterns",
                    "url": "https://example.com/python-async",
                    "description": "A guide to async patterns in Python.",
                },
                {
                    "title": "Asyncio Documentation",
                    "url": "https://docs.python.org/asyncio",
                    "description": "Official asyncio docs.",
                },
            ]
        }
    }


@pytest.fixture
def brave_response_empty():
    return {"web": {"results": []}}


@pytest.fixture
def serper_response_ok():
    return {
        "organic": [
            {
                "title": "Python Async Patterns",
                "link": "https://example.com/python-async",
                "snippet": "A guide to async patterns in Python.",
            },
            {
                "title": "Asyncio Documentation",
                "link": "https://docs.python.org/asyncio",
                "snippet": "Official asyncio docs.",
            },
        ],
        "knowledgeGraph": {
            "title": "Python",
            "description": "A programming language.",
        },
    }


@pytest.fixture
def serper_response_empty():
    return {"organic": []}
