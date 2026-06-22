#!/usr/bin/env python3
"""
Trishula-Scraper: Sovereign Pure-Python HTML-to-Markdown Scraper & Crawler
Zero dependencies. Local-first. Optimized for sports data and tables.
"""

import urllib.request
import urllib.parse
import urllib.error
import random
import re
import sys
import argparse
from html.parser import HTMLParser
from typing import Optional, List, Dict, Set

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/21010101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

VOID_ELEMENTS = {"img", "br", "hr", "input", "meta", "link", "source", "area", "base", "col", "embed", "param", "track", "wbr"}
IGNORE_TAGS = {"script", "style", "nav", "footer", "header", "aside", "form", "button", "iframe", "noscript", "head"}
BLOCK_PARENT_TAGS = {"ul", "ol", "table", "thead", "tbody", "tr", "root", "html", "body"}

class Node:
    """Represents a simplified DOM node for Markdown rendering."""
    def __init__(self, tag: str, attrs: Optional[List[tuple]] = None, text: str = ""):
        self.tag = tag.lower()
        self.attrs = dict(attrs) if attrs else {}
        self.text = text
        self.children: List['Node'] = []

class DOMBuilder(HTMLParser):
    """Parses HTML into a tree of Node instances, ignoring specified elements."""
    def __init__(self, ignore_tags: Set[str] = IGNORE_TAGS):
        super().__init__()
        self.root = Node("root")
        self.stack = [self.root]
        self.ignore_tags = ignore_tags
        self.in_pre = False

    def handle_starttag(self, tag: str, attrs: List[tuple]):
        tag_lower = tag.lower()
        if tag_lower == "pre":
            self.in_pre = True
        if tag_lower in self.ignore_tags:
            self.stack.append(None)  # Sentinel representing an ignored sub-tree
            return
        if self.stack[-1] is None:
            self.stack.append(None)
            return

        node = Node(tag_lower, attrs)
        self.stack[-1].children.append(node)
        if tag_lower not in VOID_ELEMENTS:
            self.stack.append(node)

    def handle_endtag(self, tag: str):
        tag_lower = tag.lower()
        if tag_lower == "pre":
            self.in_pre = False
        if tag_lower in self.ignore_tags:
            if self.stack:
                self.stack.pop()
            return
        if self.stack[-1] is None:
            if self.stack:
                self.stack.pop()
            return

        if self.stack[-1].tag == tag_lower:
            self.stack.pop()
        else:
            # Handle mismatched tags gracefully by popping back to matching parent
            for i in range(len(self.stack) - 1, 0, -1):
                if self.stack[i] and self.stack[i].tag == tag_lower:
                    while len(self.stack) > i:
                        self.stack.pop()
                    break

    def handle_data(self, data: str):
        if self.stack[-1] is not None:
            if self.in_pre:
                text_node = Node("text", text=data)
                self.stack[-1].children.append(text_node)
            else:
                tag = self.stack[-1].tag
                if tag in BLOCK_PARENT_TAGS:
                    if data.strip():
                        collapsed = re.sub(r'\s+', ' ', data)
                        text_node = Node("text", text=collapsed)
                        self.stack[-1].children.append(text_node)
                else:
                    collapsed = re.sub(r'\s+', ' ', data)
                    if collapsed and collapsed != ' ':
                        text_node = Node("text", text=collapsed)
                        self.stack[-1].children.append(text_node)
                    elif collapsed == ' ':
                        children = self.stack[-1].children
                        if not children or children[-1].tag != "text" or not children[-1].text.endswith(" "):
                            text_node = Node("text", text=" ")
                            self.stack[-1].children.append(text_node)

def fetch_html(url: str, timeout: int = 10, user_agent: Optional[str] = None) -> str:
    """Fetch HTML content from a URL using standard library urllib."""
    if not user_agent:
        user_agent = random.choice(USER_AGENTS)

    req = urllib.request.Request(
        url,
        headers={"User-Agent": user_agent}
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            charset = "utf-8"
            if "charset=" in content_type:
                charset = content_type.split("charset=")[-1].strip()

            html_bytes = response.read()
            try:
                return html_bytes.decode(charset)
            except LookupError:
                return html_bytes.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP Error {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Failed to reach server: {e.reason}")
    except Exception as e:
        raise RuntimeError(f"Error fetching URL: {str(e)}")

def render_table(table_node: Node, base_url: Optional[str], no_links: bool) -> str:
    """Converts a <table> Node into a clean, aligned Markdown table."""
    rows: List[List[str]] = []
    row_is_header: List[bool] = []

    def find_rows(node: Node):
        if node.tag == "tr":
            row_cells = []
            is_header = True
            for cell in node.children:
                if cell.tag in ("th", "td"):
                    if cell.tag == "td":
                        is_header = False
                    colspan = 1
                    if "colspan" in cell.attrs:
                        try:
                            colspan = int(cell.attrs["colspan"])
                        except ValueError:
                            colspan = 1
                    cell_text = render_node(cell, base_url, no_links).strip()
                    cell_text = cell_text.replace('|', '\\|')
                    # Strip internal newlines/carriage returns to maintain row alignment
                    cell_text = re.sub(r'\s+', ' ', cell_text)
                    row_cells.append(cell_text)
                    for _ in range(colspan - 1):
                        row_cells.append("")
            if row_cells:
                rows.append(row_cells)
                row_is_header.append(is_header)
        else:
            for child in node.children:
                find_rows(child)

    find_rows(table_node)
    if not rows:
        return ""

    # Column count is the max count of cells in any row
    col_count = max(len(row) for row in rows)

    # Pad shorter rows
    for row in rows:
        while len(row) < col_count:
            row.append("")

    # Determine maximum column widths (minimum width of 3 to support standard MD alignment headers)
    col_widths = [3] * col_count
    for row in rows:
        for idx, cell in enumerate(row):
            col_widths[idx] = max(col_widths[idx], len(cell))

    markdown_lines = []

    # Check for th-based header
    has_header = any(row_is_header)
    if has_header:
        header_idx = row_is_header.index(True)
        header_row = rows[header_idx]
        data_rows = [r for i, r in enumerate(rows) if i != header_idx]
    else:
        # Fallback: treat the first row as the header
        header_row = rows[0]
        data_rows = rows[1:]

    # Header line
    header_line = "| " + " | ".join(cell.ljust(col_widths[i]) for i, cell in enumerate(header_row)) + " |"
    markdown_lines.append(header_line)

    # Separator line
    separator_line = "| " + " | ".join("-" * col_widths[i] for i in range(col_count)) + " |"
    markdown_lines.append(separator_line)

    # Data lines
    for row in data_rows:
        row_line = "| " + " | ".join(cell.ljust(col_widths[i]) for i, cell in enumerate(row)) + " |"
        markdown_lines.append(row_line)

    return "\n\n" + "\n".join(markdown_lines) + "\n\n"

def render_node(node: Node, base_url: Optional[str] = None, no_links: bool = False, list_depth: int = 0) -> str:
    """Recursively converts a Node DOM tree to clean Markdown."""
    if not node:
        return ""

    if node.tag == "text":
        return node.text

    child_contents = []
    for child in node.children:
        child_contents.append(render_node(child, base_url, no_links, list_depth))
    content = "".join(child_contents)

    tag = node.tag
    if tag == "root":
        return content.strip()

    if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        level = int(tag[1])
        return f"\n\n{'#' * level} {content.strip()}\n\n"

    if tag == "p":
        return f"\n\n{content.strip()}\n\n"

    if tag == "br":
        return "  \n"

    if tag == "hr":
        return "\n\n---\n\n"

    if tag in ("strong", "b"):
        stripped = content.strip()
        return f"**{stripped}**" if stripped else ""

    if tag in ("em", "i"):
        stripped = content.strip()
        return f"*{stripped}*" if stripped else ""

    if tag == "code":
        return f"`{content}`"

    if tag == "pre":
        return f"\n\n```\n{content}\n```\n\n"

    if tag == "blockquote":
        lines = content.strip().split("\n")
        quoted = "\n".join(f"> {line}" for line in lines)
        return f"\n\n{quoted}\n\n"

    if tag == "a":
        href = node.attrs.get("href", "")
        text = content.strip()
        if href and not no_links:
            if base_url:
                href = urllib.parse.urljoin(base_url, href)
            if not text:
                return f" <{href}> "
            return f" [{text}]({href}) "
        return text

    if tag == "ul":
        items = []
        for child in node.children:
            if child.tag == "li":
                item_text = render_node(child, base_url, no_links, list_depth + 1).strip()
                if item_text:
                    indent = "  " * list_depth
                    items.append(f"{indent}- {item_text}\n")
            else:
                items.append(render_node(child, base_url, no_links, list_depth))
        return "\n" + "".join(items) + "\n"

    if tag == "ol":
        items = []
        index = 1
        for child in node.children:
            if child.tag == "li":
                item_text = render_node(child, base_url, no_links, list_depth + 1).strip()
                if item_text:
                    indent = "  " * list_depth
                    items.append(f"{indent}{index}. {item_text}\n")
                    index += 1
            else:
                items.append(render_node(child, base_url, no_links, list_depth))
        return "\n" + "".join(items) + "\n"

    if tag == "li":
        return content

    if tag == "img":
        src = node.attrs.get("src", "")
        alt = node.attrs.get("alt", "Image")
        if src:
            if src.startswith("data:"):
                return f" ![{alt}]([Base64 Data]) "
            if base_url:
                src = urllib.parse.urljoin(base_url, src)
            return f" ![{alt}]({src}) "
        return ""

    if tag == "table":
        return render_table(node, base_url, no_links)

    return content

def extract_tables_only(node: Node, base_url: Optional[str], no_links: bool) -> str:
    """Finds and renders only <table> elements within the DOM tree."""
    tables = []

    def scan(n: Node):
        if n.tag == "table":
            tables.append(render_table(n, base_url, no_links))
        else:
            for child in n.children:
                scan(child)

    scan(node)
    return "\n\n".join(tables).strip()

def clean_markdown(md_text: str) -> str:
    """Normalizes excessive newlines and whitespace in output markdown."""
    # Replace non-breaking spaces with standard spaces
    md_text = md_text.replace('\xa0', ' ')
    # Compress 3+ newlines to exactly 2
    cleaned = re.sub(r'\n{3,}', '\n\n', md_text)
    
    # Process line by line to clean trailing whitespaces safely
    lines = []
    for line in cleaned.splitlines():
        if line.endswith("  ") and not line.endswith("   "):
            lines.append(line.rstrip() + "  ")
        else:
            lines.append(line.rstrip())
    return "\n".join(lines).strip()

def html_to_markdown(html_content: str, base_url: Optional[str] = None, no_links: bool = False, only_tables: bool = False) -> str:
    """Converts raw HTML string to formatted Markdown."""
    parser = DOMBuilder()
    parser.feed(html_content)
    
    if only_tables:
        raw_md = extract_tables_only(parser.root, base_url, no_links)
    else:
        raw_md = render_node(parser.root, base_url, no_links)
        
    return clean_markdown(raw_md)

def scrape(url: str, timeout: int = 10, no_links: bool = False, only_tables: bool = False) -> str:
    """Fetch URL and convert the page HTML content into Markdown."""
    html = fetch_html(url, timeout=timeout)
    return html_to_markdown(html, base_url=url, no_links=no_links, only_tables=only_tables)

def main():
    parser = argparse.ArgumentParser(description="Trishula-Scraper: Sovereign Pure-Python HTML-to-Markdown Scraper")
    parser.add_argument("url", help="Webpage URL to fetch and scrape")
    parser.add_argument("-o", "--output", help="File path to write output markdown")
    parser.add_argument("-t", "--only-tables", action="store_true", help="Extract only tables from the page")
    parser.add_argument("--no-links", action="store_true", help="Do not output links in markdown (extract anchor text only)")
    parser.add_argument("--timeout", type=int, default=10, help="Webpage connection timeout in seconds (default: 10)")

    args = parser.parse_args()

    try:
        markdown = scrape(args.url, timeout=args.timeout, no_links=args.no_links, only_tables=args.only_tables)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(markdown)
            print(f"✅ Successfully wrote markdown output to: {args.output}")
        else:
            print(markdown)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
