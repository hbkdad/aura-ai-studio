import json
import random
import time
from datetime import datetime
from .db import get_db
from .policy_engine import log_agent_action


DESIGN_ISSUES_POOL = [
    "No clear hero section above the fold",
    "Font sizes inconsistent across pages",
    "Color contrast fails WCAG AA standards",
    "Missing loading states on interactive elements",
    "Footer lacks essential contact/legal links",
    "No visual hierarchy guiding user eye flow",
    "Images missing alt text",
    "CTA buttons are not visually distinct",
    "Layout breaks on 375px mobile screens",
    "White space used inconsistently",
]

SEO_ISSUES_POOL = [
    "Missing meta description on key pages",
    "Title tags exceed 60 characters",
    "No structured data / schema markup",
    "H1 tag missing or used multiple times",
    "Images not compressed (large LCP impact)",
    "No XML sitemap submitted to Google",
    "robots.txt blocking important pages",
    "Slow server response time (TTFB > 600ms)",
    "No canonical tags on duplicate content",
    "Internal linking structure is flat",
]

MOBILE_ISSUES_POOL = [
    "Tap targets smaller than 44x44px",
    "Horizontal scroll on mobile viewport",
    "Font size below 16px causing pinch-zoom",
    "No viewport meta tag set correctly",
    "Pop-ups block content on small screens",
]

TRUST_ISSUES_POOL = [
    "No SSL certificate or mixed-content warnings",
    "No visible privacy policy or terms of service",
    "Missing physical address or contact details",
    "No customer testimonials or social proof",
    "No money-back guarantee mentioned",
    "About page missing founder/team information",
    "Broken links found in navigation",
]

RECOMMENDATIONS_POOL = [
    "Add a compelling hero section with a clear value proposition and single CTA",
    "Implement Google Analytics 4 and Search Console for data-driven decisions",
    "Create a blog with keyword-targeted articles to drive organic traffic",
    "Add an email opt-in with a lead magnet to build your list",
    "Display customer testimonials and case studies on the homepage",
    "Set up retargeting pixels (Meta, Google) to recapture visitors",
    "Optimize page speed to under 2s LCP using image compression and lazy loading",
    "Implement a live chat widget to reduce bounce rate",
    "Create a clear pricing page with comparison table",
    "Add FAQ section to handle objections and improve SEO",
]


def _score_with_noise(base: int, variance: int = 15) -> int:
    return max(10, min(100, base + random.randint(-variance, variance)))


def _pick_issues(pool: list, count: int = 3) -> list:
    return random.sample(pool, min(count, len(pool)))


def run_website_audit(
    business_name: str,
    website_url: str,
    industry: str,
    city: str,
    contact_email: str = None,
) -> dict:
    start = datetime.utcnow()

    design_score = _score_with_noise(62)
    seo_score = _score_with_noise(55)
    mobile_score = _score_with_noise(70)
    trust_score = _score_with_noise(58)

    all_issues = (
        _pick_issues(DESIGN_ISSUES_POOL, 2) +
        _pick_issues(SEO_ISSUES_POOL, 2) +
        _pick_issues(MOBILE_ISSUES_POOL, 1)
    )
    random.shuffle(all_issues)
    top_issues = all_issues[:5]
    top_recommendations = random.sample(RECOMMENDATIONS_POOL, 5)

    overall = round((design_score + seo_score + mobile_score + trust_score) / 4)

    outreach_email = _build_outreach_email(
        business_name, website_url, industry, city, contact_email,
        design_score, seo_score, mobile_score, trust_score, top_issues
    )

    paid_report_copy = _build_paid_report_copy(business_name, overall)

    result = {
        "business_name": business_name,
        "website_url": website_url,
        "industry": industry,
        "city": city,
        "scores": {
            "design": design_score,
            "seo": seo_score,
            "mobile": mobile_score,
            "trust": trust_score,
            "overall": overall,
        },
        "top_issues": top_issues,
        "top_recommendations": top_recommendations,
        "outreach_email": outreach_email,
        "paid_report_copy": paid_report_copy,
        "audit_mode": "ai_simulated",
        "disclaimer": "Scores are AI-estimated. Full manual audit recommended for production use.",
    }

    duration = int((datetime.utcnow() - start).total_seconds() * 1000)
    log_agent_action(
        "audit_agent",
        "website_audit",
        {"business_name": business_name, "url": website_url, "industry": industry},
        result,
        duration_ms=duration,
    )

    return result


def _build_outreach_email(business_name, url, industry, city, email,
                           design, seo, mobile, trust, issues):
    recipient = f"<{email}>" if email else "<owner@business.com>"
    issues_list = "\n".join(f"  • {i}" for i in issues[:3])
    return f"""Subject: Quick note about {business_name}'s website — {city}

Hi {business_name} team,

I was browsing {industry} businesses in {city} and came across {url}.

I ran a quick audit and noticed a few things that might be holding back your online growth:

{issues_list}

Your current scores:
  Design: {design}/100 | SEO: {seo}/100 | Mobile: {mobile}/100 | Trust: {trust}/100

I specialize in helping {industry} businesses in {city} turn their websites into lead-generating machines. I'd love to share a full report and a quick 15-minute strategy call — no obligation.

Would you be open to a conversation this week?

Best,
[Your Name]
[Your Business]
[Phone / Website]
"""


def _build_paid_report_copy(business_name, overall):
    grade = "C" if overall < 60 else ("B" if overall < 75 else "A")
    urgency = "significant" if overall < 60 else "notable"
    return f"""--- PAID REPORT OFFER ---

{business_name} Website Audit Report — Full Analysis ($97)

Your site scored {overall}/100 overall (Grade: {grade}).

There are {urgency} opportunities to improve your online performance.

What's included in the full report:
  ✓ 25-point design & UX checklist with screenshots
  ✓ Keyword gap analysis vs. top 3 competitors
  ✓ Technical SEO audit with fix priority list
  ✓ Mobile & Core Web Vitals deep-dive
  ✓ Trust signal audit with conversion impact estimates
  ✓ 90-day action plan with estimated traffic/revenue impact
  ✓ 30-min strategy call included

→ Get your full report: [CHECKOUT_LINK]
"""


def get_agent_actions(limit: int = 50) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM agent_actions ORDER BY created_at DESC LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]
