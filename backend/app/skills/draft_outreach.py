NAME = "draft_outreach"
DESCRIPTION = "Generates a cold outreach email for a prospect business"
REQUIRED_INPUTS = ["business_name", "industry", "city"]
INPUT_SCHEMA = {
    "business_name": "str (required) — name of the target business",
    "industry": "str (required) — business industry",
    "city": "str (required) — business city/location",
    "website_url": "str (optional) — business website",
    "issues": "list[str] (optional) — known pain points to reference",
}
OUTPUT_SCHEMA = {
    "subject": "str — email subject line",
    "body": "str — full email body",
}


def run(input: dict) -> dict:
    business_name = input.get("business_name", "").strip()
    industry = input.get("industry", "").strip()
    city = input.get("city", "").strip()
    website_url = input.get("website_url", "your website")
    issues = input.get("issues", [])

    if not all([business_name, industry, city]):
        raise ValueError("business_name, industry, and city are required inputs")

    issues_block = ""
    if issues:
        issues_block = "\n\nI noticed a few things that might be holding back your growth:\n"
        issues_block += "\n".join(f"  • {i}" for i in issues[:3])

    subject = f"Quick note about {business_name}'s online presence — {city}"
    body = (
        f"Hi {business_name} team,\n\n"
        f"I was browsing {industry} businesses in {city} and came across {website_url}."
        f"{issues_block}\n\n"
        f"I specialize in helping {industry} businesses in {city} turn their websites "
        f"into lead-generating machines. I'd love to share a quick audit and a 15-minute "
        f"strategy call — no obligation.\n\n"
        f"Would you be open to a conversation this week?\n\n"
        f"Best,\n[Your Name]\n[Your Business]\n[Phone / Website]"
    )
    return {"subject": subject, "body": body}
