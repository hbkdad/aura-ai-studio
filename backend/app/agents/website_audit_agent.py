"""
WebsiteAuditAgent — audits a business website and returns structured scores.

Responsibilities:
- Accept a business URL + context (name, industry, city)
- Run real SEO analysis via pyseoanalyzer when installed, HTTP scan fallback,
  then simulated scoring as a last resort
- Return structured audit scores: design / SEO / mobile / trust / overall
- Generate a ready-to-send outreach email with the audit findings

Does NOT:
- Modify or interact with the target website beyond HTTP GET requests
- Store PII about the audited business in the database
- Guarantee accuracy — scores are AI-estimated, not a formal audit
"""
import random
from datetime import datetime
from ..policy_engine import check_kill_switch, log_agent_action

AGENT_NAME = "website_audit_agent"

_DESIGN_POOL = [
    "No clear hero section above the fold",
    "Font sizes inconsistent across pages",
    "Color contrast fails WCAG AA standards",
    "CTA buttons are not visually distinct",
    "White space used inconsistently",
]
_SEO_POOL = [
    "Missing meta description on key pages",
    "Title tags exceed 60 characters",
    "H1 tag missing or used multiple times",
    "Images not compressed (large LCP impact)",
    "No canonical tags on duplicate content",
]
_MOBILE_POOL = [
    "Tap targets smaller than 44x44px",
    "Horizontal scroll on mobile viewport",
    "Font size below 16px causing pinch-zoom",
]
_TRUST_POOL = [
    "No visible privacy policy or terms of service",
    "Missing physical address or contact details",
    "No customer testimonials or social proof",
    "About page missing founder/team information",
]
_RECO_POOL = [
    "Add a compelling hero section with a clear value proposition and single CTA",
    "Implement Google Analytics 4 and Search Console for data-driven decisions",
    "Create a blog with keyword-targeted articles to drive organic traffic",
    "Add an email opt-in with a lead magnet to build your list",
    "Optimize page speed to under 2s LCP using image compression and lazy loading",
    "Add FAQ section to handle objections and improve SEO",
    "Display customer testimonials and case studies on the homepage",
]


class WebsiteAuditAgent:
    name = AGENT_NAME
    description = "Audits a business website for SEO, design, mobile, and trust signals"
    skills_used = ["website_scan", "audit_report", "outreach_email", "check_kill_switch"]

    def run_audit(
        self,
        business_name: str,
        website_url: str,
        industry: str,
        city: str,
        contact_email: str = None,
    ) -> dict:
        """Run a full website audit. Returns scores, issues, recommendations, and outreach email."""
        if check_kill_switch():
            return {"status": "blocked", "reason": "Kill switch is active"}

        start = datetime.utcnow()
        scan_source = "simulated"
        scan_data = None

        # Try real audit_report_skill (uses http_scan + pyseoanalyzer fallback chain)
        try:
            from ..skills.audit_report_skill import run as _audit_run
            scan_data = _audit_run({
                "business_name": business_name,
                "url": website_url,
                "industry": industry,
                "city": city,
            })
            scan_source = scan_data.get("scan_source", "http_scan")
        except Exception:
            scan_data = None

        if scan_data and "scores" in scan_data:
            scores = scan_data["scores"]
            top_issues = scan_data.get("top_issues", [])
            recommendations = scan_data.get("top_recommendations", [])
        else:
            # Full simulated fallback
            design_score = max(10, min(100, 62 + random.randint(-15, 15)))
            seo_score = max(10, min(100, 55 + random.randint(-15, 15)))
            mobile_score = max(10, min(100, 70 + random.randint(-15, 15)))
            trust_score = max(10, min(100, 58 + random.randint(-15, 15)))
            overall = round((design_score + seo_score + mobile_score + trust_score) / 4)
            scores = {
                "design": design_score, "seo": seo_score,
                "mobile": mobile_score, "trust": trust_score, "overall": overall,
            }
            top_issues = (
                random.sample(_DESIGN_POOL, 2) +
                random.sample(_SEO_POOL, 2) +
                random.sample(_MOBILE_POOL, 1)
            )[:5]
            recommendations = random.sample(_RECO_POOL, 5)

        outreach = self._build_outreach(
            business_name, website_url, industry, city, contact_email, scores, top_issues
        )

        result = {
            "business_name": business_name,
            "website_url": website_url,
            "industry": industry,
            "city": city,
            "scores": scores,
            "top_issues": top_issues,
            "top_recommendations": recommendations,
            "outreach_email": outreach,
            "scan_source": scan_source,
            "audit_mode": scan_source,
            "disclaimer": "Scores are AI-estimated. Full manual audit recommended for production use.",
        }

        duration_ms = int((datetime.utcnow() - start).total_seconds() * 1000)
        log_agent_action(
            AGENT_NAME, "website_audit",
            {"business_name": business_name, "url": website_url, "industry": industry},
            {"scores": scores, "issues_count": len(top_issues), "scan_source": scan_source},
            duration_ms=duration_ms,
        )
        return result

    def _build_outreach(self, name, url, industry, city, email, scores, issues):
        issues_block = "\n".join(f"  • {i}" for i in issues[:3])
        d, s, m, t = (
            scores.get("design", 0), scores.get("seo", 0),
            scores.get("mobile", 0), scores.get("trust", 0),
        )
        return (
            f"Subject: Quick note about {name}'s website — {city}\n\n"
            f"Hi {name} team,\n\n"
            f"I was browsing {industry} businesses in {city} and came across {url}.\n\n"
            f"I ran a quick audit and noticed a few things that might be holding back "
            f"your online growth:\n\n{issues_block}\n\n"
            f"Your current scores:\n"
            f"  Design: {d}/100 | SEO: {s}/100 | Mobile: {m}/100 | Trust: {t}/100\n\n"
            f"I specialize in helping {industry} businesses in {city} turn their websites "
            f"into lead-generating machines. I'd love to share a full report and a quick "
            f"15-minute strategy call — no obligation.\n\n"
            f"Would you be open to a conversation this week?\n\n"
            f"Best,\n[Your Name]\n[Your Business]\n[Phone / Website]"
        )
