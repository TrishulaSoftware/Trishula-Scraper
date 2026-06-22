import unittest
from unittest.mock import patch, MagicMock
import urllib.error
import io

from trishula_scraper import (
    Node, DOMBuilder, html_to_markdown, fetch_html, scrape
)

class TestDOMBuilder(unittest.TestCase):
    def test_dom_tree_basic(self):
        html = "<html><body><h1>Title</h1><p>Paragraph <strong>bold</strong> text.</p></body></html>"
        parser = DOMBuilder()
        parser.feed(html)
        root = parser.root
        
        self.assertEqual(len(root.children), 1)  # html node
        body = root.children[0]
        self.assertEqual(body.tag, "html")
        
        # DOMBuilder doesn't filter html/body unless ignored
        # Let's inspect deep rendering
        md = html_to_markdown(html)
        self.assertIn("# Title", md)
        self.assertIn("Paragraph **bold** text.", md)

    def test_boilerplate_pruning(self):
        html = """
        <html>
            <head><title>Test Page</title><style>body { color: red; }</style></head>
            <body>
                <header>Navigation Header</header>
                <nav><a href="/home">Home</a></nav>
                <main>
                    <h1>Actual Content</h1>
                    <p>This is what we want.</p>
                </main>
                <aside>Related Links</aside>
                <footer>Footer Notice</footer>
                <script>console.log('hello');</script>
            </body>
        </html>
        """
        md = html_to_markdown(html)
        self.assertNotIn("Navigation Header", md)
        self.assertNotIn("Home", md)
        self.assertNotIn("Related Links", md)
        self.assertNotIn("Footer Notice", md)
        self.assertNotIn("console.log", md)
        self.assertIn("# Actual Content", md)
        self.assertIn("This is what we want.", md)

class TestMarkdownRendering(unittest.TestCase):
    def test_basic_formatting(self):
        html = "<p>This is <strong>strong</strong>, <em>italic</em>, and <code>code</code>.</p>"
        md = html_to_markdown(html)
        self.assertEqual(md, "This is **strong**, *italic*, and `code`.")

    def test_headings_and_hr(self):
        html = "<h1>Header 1</h1><hr><h2>Header 2</h2>"
        md = html_to_markdown(html)
        self.assertEqual(md, "# Header 1\n\n---\n\n## Header 2")

    def test_links(self):
        html = '<p>Check out <a href="/sports">Sports Section</a> or empty <a href="http://pinnacle.com"></a>.</p>'
        
        # Absolute resolution using base URL
        md = html_to_markdown(html, base_url="http://trishula.local/dashboard")
        self.assertIn("[Sports Section](http://trishula.local/sports)", md)
        self.assertIn("<http://pinnacle.com>", md)

        # No links flag
        md_no_links = html_to_markdown(html, no_links=True)
        self.assertEqual(md_no_links, "Check out Sports Section or empty .")

    def test_lists(self):
        html = """
        <ul>
            <li>Item A</li>
            <li>Item B
                <ol>
                    <li>Sub 1</li>
                    <li>Sub 2</li>
                </ol>
            </li>
        </ul>
        """
        md = html_to_markdown(html)
        expected = "- Item A\n- Item B\n  1. Sub 1\n  2. Sub 2"
        self.assertEqual(md, expected)

    def test_blockquote(self):
        html = "<blockquote>This is a quote.<br>Line 2.</blockquote>"
        md = html_to_markdown(html)
        self.assertEqual(md, "> This is a quote.  \n> Line 2.")

    def test_image_rendering(self):
        html = '<p><img src="/images/logo.png" alt="Trishula Logo"> and <img src="data:image/png;base64,iVBORw0KGgoAAA" alt="Inline Pic"></p>'
        md = html_to_markdown(html, base_url="http://trishula.local")
        self.assertIn("![Trishula Logo](http://trishula.local/images/logo.png)", md)
        self.assertIn("![Inline Pic]([Base64 Data])", md)

    def test_non_breaking_spaces(self):
        html = "<p>Word1&nbsp;Word2</p>"
        md = html_to_markdown(html)
        self.assertEqual(md, "Word1 Word2")

    def test_skip_empty_list_items(self):
        html = "<ul><li>Item</li><li></li><li>  </li></ul>"
        md = html_to_markdown(html)
        self.assertEqual(md, "- Item")

class TestTableRendering(unittest.TestCase):
    def test_simple_table(self):
        html = """
        <table>
            <thead>
                <tr>
                    <th>Runner</th>
                    <th>Odds</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Blue Storm</td>
                    <td>+150</td>
                </tr>
                <tr>
                    <td>Old Yeller</td>
                    <td>+300</td>
                </tr>
            </tbody>
        </table>
        """
        md = html_to_markdown(html)
        self.assertIn("| Runner     | Odds |", md)
        self.assertIn("| ---------- | ---- |", md)
        self.assertIn("| Blue Storm | +150 |", md)
        self.assertIn("| Old Yeller | +300 |", md)

    def test_uneven_table_padding(self):
        # Row 2 only has 1 cell instead of 2
        html = """
        <table>
            <tr>
                <th>Col A</th>
                <th>Col B</th>
            </tr>
            <tr>
                <td>Data A</td>
            </tr>
        </table>
        """
        md = html_to_markdown(html)
        self.assertIn("| Col A  | Col B |", md)
        self.assertIn("| Data A |       |", md)

    def test_only_tables_filter(self):
        html = """
        <h1>Main Report</h1>
        <p>Text to exclude.</p>
        <table>
            <tr><th>Header</th></tr>
            <tr><td>Cell</td></tr>
        </table>
        """
        md = html_to_markdown(html, only_tables=True)
        self.assertNotIn("Main Report", md)
        self.assertNotIn("Text to exclude", md)
        self.assertIn("| Header |", md)
        self.assertIn("| Cell   |", md)

    def test_table_pipe_escaping(self):
        html = """
        <table>
            <tr><th>Team | Player</th></tr>
            <tr><td>Lakers | LeBron</td></tr>
        </table>
        """
        md = html_to_markdown(html)
        self.assertIn("Team \\| Player", md)
        self.assertIn("Lakers \\| LeBron", md)

    def test_table_colspan(self):
        html = """
        <table>
            <tr><th>Col A</th><th>Col B</th></tr>
            <tr><td colspan="2">Merged Cell</td></tr>
        </table>
        """
        md = html_to_markdown(html)
        self.assertIn("Col A", md)
        self.assertIn("Col B", md)
        self.assertIn("Merged Cell", md)

class TestFetcherAndNetwork(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_fetch_html_success(self, mock_urlopen):
        # Configure mock response
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "text/html; charset=utf-8"}
        mock_response.read.return_value = b"<html><body><p>Hello World</p></body></html>"
        mock_urlopen.return_value.__enter__.return_value = mock_response

        html = fetch_html("http://mockurl.com")
        self.assertEqual(html, "<html><body><p>Hello World</p></body></html>")
        mock_urlopen.assert_called_once()

    @patch("urllib.request.urlopen")
    def test_fetch_html_http_error(self, mock_urlopen):
        # Configure mock to raise HTTPError
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "http://mockurl.com", 403, "Forbidden", {}, None
        )
        with self.assertRaises(RuntimeError) as context:
            fetch_html("http://mockurl.com")
        self.assertIn("HTTP Error 403", str(context.exception))

    @patch("urllib.request.urlopen")
    def test_scrape_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.read.return_value = b"<h1>Title</h1>"
        mock_urlopen.return_value.__enter__.return_value = mock_response

        md = scrape("http://mockurl.com")
        self.assertEqual(md, "# Title")

if __name__ == "__main__":
    unittest.main()
