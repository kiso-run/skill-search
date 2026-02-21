from unittest.mock import MagicMock, patch

import httpx
import pytest

from run import format_results, search_serper


def make_response(data, status_code=200):
    mock = MagicMock(spec=httpx.Response)
    mock.status_code = status_code
    mock.json.return_value = data
    if status_code >= 400:
        mock.raise_for_status.side_effect = httpx.HTTPStatusError(
            f"HTTP {status_code}", request=MagicMock(), response=mock
        )
        mock.text = f"error {status_code}"
    else:
        mock.raise_for_status.return_value = None
    return mock


class TestSearchSerper:
    def test_valid_response_parses_results(self, serper_response_ok):
        with patch("httpx.post", return_value=make_response(serper_response_ok)):
            results = search_serper("python async", 5, None, None, "key123")
        assert len(results) == 2
        assert results[0]["title"] == "Python Async Patterns"
        assert results[0]["url"] == "https://example.com/python-async"
        assert results[0]["snippet"] == "A guide to async patterns in Python."

    def test_empty_organic_returns_empty(self, serper_response_empty):
        with patch("httpx.post", return_value=make_response(serper_response_empty)):
            results = search_serper("nothing", 5, None, None, "key123")
        assert results == []
        output = format_results("nothing", results)
        assert output == 'No results found for "nothing".'

    def test_http_401_raises(self):
        with patch("httpx.post", return_value=make_response({}, 401)):
            with pytest.raises(httpx.HTTPStatusError):
                search_serper("query", 5, None, None, "bad-key")

    def test_http_429_raises(self):
        with patch("httpx.post", return_value=make_response({}, 429)):
            with pytest.raises(httpx.HTTPStatusError):
                search_serper("query", 5, None, None, "key123")

    def test_http_500_raises(self):
        with patch("httpx.post", return_value=make_response({}, 500)):
            with pytest.raises(httpx.HTTPStatusError):
                search_serper("query", 5, None, None, "key123")

    def test_language_lowercased(self, serper_response_ok):
        with patch("httpx.post", return_value=make_response(serper_response_ok)) as mock_post:
            search_serper("query", 5, "IT", None, "key123")
            body = mock_post.call_args[1]["json"]
            assert body["hl"] == "it"

    def test_country_lowercased(self, serper_response_ok):
        with patch("httpx.post", return_value=make_response(serper_response_ok)) as mock_post:
            search_serper("query", 5, None, "US", "key123")
            body = mock_post.call_args[1]["json"]
            assert body["gl"] == "us"

    def test_language_and_country_lowercased(self, serper_response_ok):
        with patch("httpx.post", return_value=make_response(serper_response_ok)) as mock_post:
            search_serper("query", 3, "JA", "JP", "key123")
            body = mock_post.call_args[1]["json"]
            assert body["hl"] == "ja"
            assert body["gl"] == "jp"
            assert body["num"] == 3

    def test_no_language_no_country_omitted(self, serper_response_ok):
        with patch("httpx.post", return_value=make_response(serper_response_ok)) as mock_post:
            search_serper("query", 5, None, None, "key123")
            body = mock_post.call_args[1]["json"]
            assert "hl" not in body
            assert "gl" not in body

    def test_knowledge_graph_ignored(self, serper_response_ok):
        with patch("httpx.post", return_value=make_response(serper_response_ok)):
            results = search_serper("python", 5, None, None, "key123")
        # Only organic results — knowledge graph must not add extra entries
        assert len(results) == 2

    def test_missing_fields_handled_gracefully(self):
        data = {"organic": [{"title": "Only Title"}]}
        with patch("httpx.post", return_value=make_response(data)):
            results = search_serper("query", 5, None, None, "key123")
        assert len(results) == 1
        assert results[0]["title"] == "Only Title"
        assert results[0]["url"] == ""
        assert results[0]["snippet"] == ""

    def test_missing_organic_key_returns_empty(self):
        with patch("httpx.post", return_value=make_response({})):
            results = search_serper("query", 5, None, None, "key123")
        assert results == []
