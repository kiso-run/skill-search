import pytest

from run import format_results


class TestFormatResults:
    def test_single_result(self):
        results = [{"title": "Example", "url": "https://example.com", "snippet": "A description."}]
        output = format_results("test", results)
        assert output == "1. Example\n   https://example.com\n   A description."

    def test_multiple_results_numbered(self):
        results = [
            {"title": "First", "url": "https://first.com", "snippet": "First snippet."},
            {"title": "Second", "url": "https://second.com", "snippet": "Second snippet."},
            {"title": "Third", "url": "https://third.com", "snippet": "Third snippet."},
        ]
        output = format_results("test", results)
        lines = output.split("\n")
        assert lines[0] == "1. First"
        assert lines[4] == "2. Second"
        assert lines[8] == "3. Third"

    def test_results_separated_by_blank_line(self):
        results = [
            {"title": "First", "url": "https://first.com", "snippet": "First."},
            {"title": "Second", "url": "https://second.com", "snippet": "Second."},
        ]
        output = format_results("test", results)
        assert "\n\n" in output

    def test_long_snippet_with_newlines_indented(self):
        snippet = "Line one.\nLine two.\nLine three."
        results = [{"title": "Title", "url": "https://example.com", "snippet": snippet}]
        output = format_results("test", results)
        assert "   Line one." in output
        assert "   Line two." in output
        assert "   Line three." in output

    def test_empty_snippet_no_blank_indented_lines(self):
        results = [{"title": "Title", "url": "https://example.com", "snippet": ""}]
        output = format_results("test", results)
        lines = output.split("\n")
        for line in lines:
            if line.startswith("   "):
                assert line.strip() != ""  # no indented blank lines

    def test_missing_snippet_key(self):
        results = [{"title": "Title", "url": "https://example.com"}]
        output = format_results("test", results)
        assert "1. Title" in output
        assert "   https://example.com" in output

    def test_no_results(self):
        output = format_results("my query", [])
        assert output == 'No results found for "my query".'

    def test_special_characters_preserved(self):
        results = [
            {
                "title": "C++ & Python: <Special> \"Chars\"",
                "url": "https://example.com/path?a=1&b=2",
                "snippet": "Snippet with 'quotes' & <tags>.",
            }
        ]
        output = format_results("special", results)
        assert "C++ & Python: <Special>" in output
        assert "path?a=1&b=2" in output
        assert "'quotes' & <tags>" in output

    def test_url_indented(self):
        results = [{"title": "Title", "url": "https://example.com", "snippet": "Snippet."}]
        output = format_results("test", results)
        lines = output.split("\n")
        assert lines[1] == "   https://example.com"

    def test_output_does_not_end_with_blank_line(self):
        results = [
            {"title": "A", "url": "https://a.com", "snippet": "Snippet A."},
            {"title": "B", "url": "https://b.com", "snippet": "Snippet B."},
        ]
        output = format_results("test", results)
        assert not output.endswith("\n")
