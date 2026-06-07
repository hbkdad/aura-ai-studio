NAME = "seo_audit"
DESCRIPTION = (
    "Crawls a website URL and returns real SEO scores, technical issues, "
    "and heading/word-count analysis using pyseoanalyzer"
)
REQUIRED_INPUTS = ["url"]
INPUT_SCHEMA = {
    "url": "str (required) — full URL to audit, e.g. https://example.com",
    "follow_links": "bool (optional, default False) — crawl inner links too",
    "analyze_headings": "bool (optional, default True) — include h1-h6 analysis",
}
OUTPUT_SCHEMA = {
    "url": "str",
    "pages_crawled": "int",
    "word_count": "int",
    "title": "str",
    "description": "str",
    "issues": "list[str] — technical SEO warnings",
    "keywords": "list — top keywords found",
    "headings": "dict — h1/h2 counts",
    "score_estimate": "int — 0-100 derived from issue count",
    "raw": "dict — full pyseoanalyzer output",
    "source": "str — always 'pyseoanalyzer'",
}

_IMPORT_ERROR: str | None = None

try:
    from pyseoanalyzer import analyze as _pyseo_analyze
except ImportError:
    _pyseo_analyze = None
    _IMPORT_ERROR = (
        "pyseoanalyzer is not installed. "
        "Run: pip install pyseoanalyzer>=2025.4.3"
    )


def run(input: dict) -> dict:
    url = input.get("url", "").strip()
    if not url:
        raise ValueError("url is required")
    if not url.startswith(("http://", "https://")):
        raise ValueError("url must start with http:// or https://")

    if _pyseo_analyze is None:
        raise RuntimeError(_IMPORT_ERROR)

    follow_links = input.get("follow_links", False)
    analyze_headings = input.get("analyze_headings", True)

    raw = _pyseo_analyze(
        url,
        follow_links=follow_links,
        analyze_headings=analyze_headings,
        analyze_extra_tags=True,
    )

    pages = raw.get("pages", [])
    first_page = pages[0] if pages else {}
    issues = raw.get("warnings", []) or first_page.get("warnings", [])
    keywords = raw.get("keywords", [])[:10]
    word_count = first_page.get("word_count", 0)
    title = first_page.get("title", "")
    description = first_page.get("description", "")
    headings = {
        "h1": len(first_page.get("h1", [])),
        "h2": len(first_page.get("h2", [])),
    }

    # Derive a simple 0-100 score: start at 100, subtract 5 per issue (floor 10)
    score_estimate = max(10, 100 - (len(issues) * 5))

    return {
        "url": url,
        "pages_crawled": len(pages),
        "word_count": word_count,
        "title": title,
        "description": description,
        "issues": [str(w) for w in issues[:10]],
        "keywords": keywords,
        "headings": headings,
        "score_estimate": score_estimate,
        "raw": raw,
        "source": "pyseoanalyzer",
    }
