# Trishula-Scraper

A lightweight, pure-Python web scraper and HTML-to-Markdown converter. Designed to offer zero-dependency, local page scraping with zero network egress.

Tailored for sports ingestion pipelines to convert raw odds sheets, spreads, and news tables into clean, aligned Markdown tables for LLM consumption.

---

## █ Features
* **Zero Dependencies**: Uses only standard Python library modules (`html.parser`, `urllib.request`).
* **Boilerplate Pruning**: Automatic stripping of `<script>`, `<style>`, `<nav>`, `<footer>`, `<header>`, `<aside>`, forms, and buttons.
* **Table Formatting**: Highly-optimized conversion of HTML tables (`<table>`, `<th>`, `<tr>`, `<td>`) to clean, aligned GitHub-flavored Markdown tables.
* **Timeout & Agent Rotation**: Implements built-in User-Agent rotation and connection timeout handling to avoid sportsbook blocks.
* **CLI-Ready**: Supports direct execution via CLI with options to save output or extract tables only.

---

## █ Installation & Requirements
* **Requirements**: Python 3.10+ (pure standard library).
* **Installation**: Drop `trishula_scraper.py` into your path or project root.

---

## █ Usage Reference

### 1. Scraping a Webpage to Markdown
Scrape a webpage and output the clean markdown directly to console:
```bash
python trishula_scraper.py https://example.com/sports-odds
```

### 2. Saving Markdown Output to File
```bash
python trishula_scraper.py https://example.com/sports-odds -o output.md
```

### 3. Extracting Tables Only
Extract only HTML tables from a page (ignoring headers, articles, and text paragraphs):
```bash
python trishula_scraper.py https://example.com/sports-odds --only-tables
```

### 4. Stripping Link URLs
To keep anchor text but strip URL suffixes (making reading text content cleaner):
```bash
python trishula_scraper.py https://example.com/sports-odds --no-links
```

### 5. Specifying Connection Timeout
```bash
python trishula_scraper.py https://example.com/sports-odds --timeout 15
```

---

## █ Running Tests
To run the included mock-based unit test suite:
```bash
python -m unittest test_trishula_scraper.py
```
