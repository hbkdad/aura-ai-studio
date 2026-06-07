"""
SalesOutreachAgent — generates personalised cold outreach emails for prospect businesses.

Responsibilities:
- Accept business context (name, industry, city) and optional audit findings
- Generate a ready-to-copy outreach email using outreach_email_skill
- Incorporate SEO scores and specific issues when available for personalisation

Does NOT:
- Send emails (no email client or SMTP in V0.1)
- Store prospect contact information
- Track email open rates or responses
- Purchase or manage contact lists
"""
from datetime import datetime
from ..policy_engine import log_agent_action

AGENT_NAME = "sales_outreach_agent"


class SalesOutreachAgent:
    name = AGENT_NAME
    description = "Generates personalised cold outreach emails from business and audit context"
    skills_used = ["outreach_email", "draft_outreach"]

    def generate(
        self,
        business_name: str,
        industry: str,
        city: str,
        website_url: str = None,
        issues: list = None,
        scores: dict = None,
    ) -> dict:
        """Generate a cold outreach email. Returns {subject, body}."""
        from ..skills.outreach_email_skill import run as _outreach_run

        if not all([business_name, industry, city]):
            raise ValueError("business_name, industry, and city are required")

        start = datetime.utcnow()
        result = _outreach_run({
            "business_name": business_name,
            "industry": industry,
            "city": city,
            "website_url": website_url or "your website",
            "issues": issues or [],
            "scores": scores or {},
        })

        duration_ms = int((datetime.utcnow() - start).total_seconds() * 1000)
        log_agent_action(
            AGENT_NAME, "generate_outreach",
            {"business_name": business_name, "industry": industry, "city": city},
            {"subject": result.get("subject", "")},
            duration_ms=duration_ms,
        )
        return result

    def generate_from_audit(self, audit_result: dict) -> dict:
        """Convenience: generate an outreach email directly from a WebsiteAuditAgent result."""
        return self.generate(
            business_name=audit_result.get("business_name", ""),
            industry=audit_result.get("industry", ""),
            city=audit_result.get("city", ""),
            website_url=audit_result.get("website_url"),
            issues=audit_result.get("top_issues"),
            scores=audit_result.get("scores"),
        )
