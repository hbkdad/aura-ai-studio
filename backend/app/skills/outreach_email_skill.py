"""
OutreachEmailSkill — generates personalised cold outreach emails with optional SEO context.

Extends draft_outreach by accepting audit scores and issues so the email
references specific findings from a recent website scan.
"""
NAME = "outreach_email"
DESCRIPTION = (
    "Generates a cold outreach email for a prospect business, optionally incorporating "
    "audit scores and specific SEO/design issues found during a website scan"
)
REQUIRED_INPUTS = ["business_name", "industry", "city"]
INPUT_SCHEMA = {
    "business_name": "str (required) — name of the target business",
    "industry": "str (required) — business industry",
    "city": "str (required) — business city/location",
    "website_url": "str (optional) — business website URL",
    "issues": "list[str] (optional) — specific issues found in audit",
    "scores": "dict (optional) — audit scores: {overall, seo, design, mobile, trust}",
}
OUTPUT_SCHEMA = {
    "subject": "str — email subject line",
    "body": "str — full email body",
}


def run(input: dict) -> dict:
    """Generate a personalised outreach email using business context and optional audit data."""
    business_name = input.get("business_name", "").strip()
    industry = input.get("industry", "").strip()
    city = input.get("city", "").strip()
    website_url = input.get("website_url", "your website")
    issues = input.get("issues") or []
    scores = input.get("scores") or {}

    if not all([business_name, industry, city]):
        raise ValueError("business_name, industry, and city are required inputs")

    # Build issues block if audit data was passed
    issues_block = ""
    if issues:
        issues_block = "\n\nI noticed a few things that might be holding back your online growth:\n"
        issues_block += "\n".join(f"  • {i}" for i in issues[:3])

    # Build score line if scores were provided
    score_line = ""
    if scores:
        overall = scores.get("overall", 0)
        seo = scores.get("seo", 0)
        grade = "C" if overall < 60 else ("B" if overall < 75 else "A")
        score_line = (
            f"\n\nYour site's current scores: Overall {overall}/100 (Grade {grade}), "
            f"SEO {seo}/100. There's real room to improve."
        )

    subject = f"Quick note about {business_name}'s online presence — {city}"
    body = (
        f"Hi {business_name} team,\n\n"
        f"I was browsing {industry} businesses in {city} and came across {website_url}."
        f"{issues_block}"
        f"{score_line}\n\n"
        f"I specialize in helping {industry} businesses in {city} turn their websites "
        f"into lead-generating machines. I'd love to share a quick audit and a 15-minute "
        f"strategy call — no obligation.\n\n"
        f"Would you be open to a conversation this week?\n\n"
        f"Best,\n[Your Name]\n[Your Business]\n[Phone / Website]"
    )

    return {"subject": subject, "body": body}
