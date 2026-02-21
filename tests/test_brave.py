from unittest.mock import MagicMock, patch

import httpx
import pytest

from run import format_results, search_brave


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


class TestSearchBrave:
    def test_valid_response_parses_results(self, brave_response_ok):
        with patch("httpx.get", return_value=make_response(brave_response_ok)):
            results = search_brave("python async", 5, None, None, "key123")
        assert len(results) == 2
        assert results[0]["title"] == "Python Async Patterns"
        assert results[0]["url"] == "https://example.com/python-async"
        assert results[0]["snippet"] == "A guide to async patterns in Python."

    def test_empty_results(self, brave_response_empty):
        with patch("httpx.get", return_value=make_response(brave_response_empty)):
            results = search_brave("nothing", 5, None, None, "key123")
        assert results == []
        output = format_results("nothing", results)
        assert output == 'No results found for "nothing".'

    def test_http_401_raises(self):
        with patch("httpx.get", return_value=make_response({}, 401)):
            with pytest.raises(httpx.HTTPStatusError):
                search_brave("query", 5, None, None, "bad-key")

    def test_http_429_raises(self):
        with patch("httpx.get", return_value=make_response({}, 429)):
            with pytest.raises(httpx.HTTPStatusError):
                search_brave("query", 5, None, None, "key123")

    def test_http_500_raises(self):
        with patch("httpx.get", return_value=make_response({}, 500)):
            with pytest.raises(httpx.HTTPStatusError):
                search_brave("query", 5, None, None, "key123")

    def test_language_param_passed(self, brave_response_ok):
        with patch("httpx.get", return_value=make_response(brave_response_ok)) as mock_get:
            search_brave("query", 5, "it", None, "key123")
            params = mock_get.call_args[1]["params"]
            assert params.get("search_lang") == "it"

    def test_country_param_passed(self, brave_response_ok):
        with patch("httpx.get", return_value=make_response(brave_response_ok)) as mock_get:
            search_brave("query", 5, None, "IT", "key123")
            call_kwargs = mock_get.call_args
            params = call_kwargs[1]["params"]
            assert params.get("country") == "IT"

    def test_language_and_country_params(self, brave_response_ok):
        with patch("httpx.get", return_value=make_response(brave_response_ok)) as mock_get:
            search_brave("query", 3, "en", "US", "key123")
            params = mock_get.call_args[1]["params"]
            assert params["search_lang"] == "en"
            assert params["country"] == "US"
            assert params["count"] == 3

    def test_no_language_no_country_params_omitted(self, brave_response_ok):
        with patch("httpx.get", return_value=make_response(brave_response_ok)) as mock_get:
            search_brave("query", 5, None, None, "key123")
            params = mock_get.call_args[1]["params"]
            assert "search_lang" not in params
            assert "country" not in params

    def test_missing_fields_handled_gracefully(self):
        data = {"web": {"results": [{"title": "Only Title"}]}}
        with patch("httpx.get", return_value=make_response(data)):
            results = search_brave("query", 5, None, None, "key123")
        assert len(results) == 1
        assert results[0]["title"] == "Only Title"
        assert results[0]["url"] == ""
        assert results[0]["snippet"] == ""

    def test_missing_web_key_returns_empty(self):
        with patch("httpx.get", return_value=make_response({})):
            results = search_brave("query", 5, None, None, "key123")
        assert results == []
