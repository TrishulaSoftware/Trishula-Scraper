# ⚜️ Trishula-Scraper
> **Sovereign Web Scraper & HTML-to-Markdown Parser**

A lightweight, zero-dependency, pure-Python web scraping and HTML-parsing engine built entirely within the Python standard library. Designed to offer local, air-gapped web content extraction, stripping bloat (scripts, style tags, navigations, ads) and formatting raw pages into clean, model-readable markdown.

Optimized for high-performance sports analytics pipelines to ingest real-time betting lines, match previews, and injury reports from public sites.

---

## █ Strategic Alignment & Features
* **Zero Dependencies**: Pure Python implementation using only standard modules (`html.parser`, `urllib.request`, `re`, `urllib.error`). Safe from supply-chain risks.
* **Aggressive Boilerplate Pruning**: Automatically prunes layout junk (`<script>`, `<style>`, `<nav>`, `<footer>`, `<header>`, `<aside>`, forms, buttons, inputs).
* **High-Fidelity Table Extraction**: Converts complex nested HTML tables (`<table>`, `<th>`, `<tr>`, `<td>`) into cleanly aligned, GFM-compliant markdown grids.
* **Anti-Block Resiliency**: Implements configurable request headers, built-in User-Agent rotation, and connection timeout rules.
* **Flexible Extraction Scopes**: Provides flags to isolate tables only, strip links (removing URL clutter while retaining text), and clean empty layout tags.

---

## █ Installation & Requirements
* **Runtime Environment**: Python 3.10, 3.11, or 3.12 (standard library).
* **Installation**: Drop `trishula_scraper.py` directly into your project root.

---

## █ Usage Reference

### Scrape Webpage to Markdown
```bash
python trishula_scraper.py https://example.com/match-data
```

### Save Scraped Output to a File
```bash
python trishula_scraper.py https://example.com/match-data -o match_stats.md
```

### Isolate HTML Tables Only
Ignore paragraphs, headers, and list items, capturing only tabular dataset elements:
```bash
python trishula_scraper.py https://example.com/betting-lines --only-tables
```

### Strip URL Anchors
Retain hyperlinked text but drop the long URL strings to save context tokens:
```bash
python trishula_scraper.py https://example.com/match-data --no-links
```

### Set Request Timeout
```bash
python trishula_scraper.py https://example.com/match-data --timeout 15
```

---

## █ Proof of Work (Verified Console Output)

The parser and parser state machines have been validated locally using mock HTTP responses and malformed markup:

```
> python test_trishula_scraper.py
..................
----------------------------------------------------------------------
Ran 18 tests in 0.007s

OK
```

---

## █ CI/CD Integration
This repository is configured with a GitHub Actions workflow (`.github/workflows/ci.yml`) validating scrapers and HTML conversion against Python versions `3.10`, `3.11`, and `3.12` on every push to the `main` branch.
