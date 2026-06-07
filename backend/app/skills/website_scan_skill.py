"""
WebsiteScanSkill — quick HTTP scan of a URL.

Fetches the page, extracts title/meta/h1 without a full crawl.
Faster and lighter than seo_audit. Use for quick prospect checks.
"""
NAME = "website_scan"
DESCRIPTION = (
    "Quick HTTP scan of a URL — extracts title, meta description, "
    "h1 count, SSL status, and basic technical issues without a full crawl"
)
REQUIRED_INPUTS = ["url"]
INPUT_SCHEMA = {
    "url": "str (required) — full URL to scan, e.g. https://example.com",
    "timeout": "int (optional, default 10) — request timeout in seconds",
}
OUTPUT_SCHEMA = {
    "url": "str",
    "status_code": "int",
    "ssl_ok": "bool",
    "title": "str",
    "description": "str",
    "h1_count": "int",
    "issues": "list[str] — basic technical issues found",
    "score_estimate": "int — 0-100 rough estimate",
    "source": "str — always 'http_scan'",
}


def run(input: dict) -> dict:
    """Fetch the page and extract basic SEO signals using only stdlib + httpx."""
    url = input.get("url", "").strip()
    if not url:
        raise ValueError("url is required")
    if not url.startswith(("http://", "https://")):
        raise ValueError("url must start with http:// or https://")

    timeout = int(input.get("timeout", 10))

    try:
        import httpx
    except ImportError:
        raise RuntimeError("httpx is not installed. Run: pip install httpx>=0.28.0")

    try:
        resp = httpx.get(url, timeout=timeout, follow_redirects=True)
    except httpx.TimeoutException:
        raise RuntimeError(f"Request timed out after {timeout}s: {url}")
    except httpx.RequestError as exc:
        raise RuntimeError(f"Failed to fetch {url}: {exc}")

    html = resp.text
    issues = []

    # Title
    import re
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip() if title_match else ""
    if not title:
        issues.append("Missing <title> tag")
    elif len(title) > 60:
        issues.append(f"Title tag too long ({len(title)} chars, max 60)")

    # Meta description
    desc_match = re.search(
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',
        html, re.IGNORECASE
    )
    if not desc_match:
        desc_match = re.search(
            r'<meta[^>]+content=["\'](.*?)["\'][^>]+name=["\']description["\']',
            html, re.IGNORECASE
        )
    description = desc_match.group(1).strip() if desc_match else ""
    if not description:
        issues.append("Missing meta description")
    elif len(description) > 160:
        issues.append(f"Meta description too long ({len(description)} chars, max 160)")

    # H1 count
    h1_matches = re.findall(r"<h1[^>]*>", html, re.IGNORECASE)
    h1_count = len(h1_matches)
    if h1_count == 0:
        issues.append("No <h1> tag found")
    elif h1_count > 1:
        issues.append(f"Multiple <h1> tags found ({h1_count}) — use only one")

    # SSL
    ssl_ok = url.startswith("https://")
    if not ssl_ok:
        issues.append("No SSL — site is served over HTTP, not HTTPS")

    # Viewport
    if "viewport" not in html.lower():
        issues.append("Missing viewport meta tag — may not render well on mobile")

    score_estimate = max(10, 100 - (len(issues) * 15))

    return {
        "url": url,
        "status_code": resp.status_code,
        "ssl_ok": ssl_ok,
        "title": title,
        "description": description,
        "h1_count": h1_count,
        "issues": issues,
        "score_estimate": score_estimate,
        "source": "http_scan",
    }
