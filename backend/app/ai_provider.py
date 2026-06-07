"""
AI provider abstraction. Selected at runtime based on environment variables:

  OPENAI_API_KEY set  → OpenAIProvider  (gpt-4o-mini)
  OLLAMA_BASE_URL set → OllamaProvider  (local LLM)
  Neither set         → PlaceholderProvider (scripted, no API key needed)

All providers implement one method:
  think(system_prompt: str, messages: list[dict]) -> str

The return value must be a JSON string the agent runner can parse:
  {"action": "skill_call", "skill": "<name>", "input": {...}}
  {"action": "done", "output": "<final answer>"}
"""
import json
import os
import logging

logger = logging.getLogger(__name__)


# ── Placeholder (no keys needed) ──────────────────────────────────────────────

_KEYWORD_SKILL_MAP = {
    "revenue":   "summarize_revenue",
    "sales":     "summarize_revenue",
    "income":    "summarize_revenue",
    "money":     "summarize_revenue",
    "btc":       "fetch_btc_price",
    "bitcoin":   "fetch_btc_price",
    "price":     "fetch_btc_price",
    "audit":     "seo_audit",
    "seo":       "seo_audit",
    "website":   "seo_audit",
    "outreach":  "draft_outreach",
    "email":     "draft_outreach",
    "pitch":     "draft_outreach",
    "kill":      "check_kill_switch",
    "safe":      "check_kill_switch",
    "status":    "check_kill_switch",
}


class PlaceholderProvider:
    """
    Scripted, deterministic provider. Works with zero API keys.
    Step 0: always check kill switch first (safety gate).
    Step 1: route to a skill based on goal keywords.
    Step 2+: if previous step produced output, return done.
    """

    name = "placeholder"

    def think(self, system_prompt: str, messages: list[dict]) -> str:
        # Count how many assistant turns have already happened
        assistant_turns = sum(1 for m in messages if m.get("role") == "assistant")

        if assistant_turns == 0:
            # First step — always check kill switch
            return json.dumps({
                "action": "skill_call",
                "skill": "check_kill_switch",
                "input": {},
            })

        if assistant_turns == 1:
            # Second step — pick skill from goal keywords
            goal = ""
            for m in messages:
                if m.get("role") == "user":
                    goal = m.get("content", "").lower()
                    break

            skill = "summarize_revenue"  # sensible default
            for keyword, mapped_skill in _KEYWORD_SKILL_MAP.items():
                if keyword in goal:
                    skill = mapped_skill
                    break

            # For skills needing inputs, pull from goal text heuristically
            skill_input: dict = {}
            if skill == "seo_audit":
                # Try to extract a URL from the goal
                words = goal.split()
                url = next((w for w in words if w.startswith("http")), None)
                if url:
                    skill_input = {"url": url}
                else:
                    # Can't run without a URL — fall back
                    skill = "summarize_revenue"
            elif skill == "draft_outreach":
                # Can't run without business_name/industry/city — fall back
                skill = "summarize_revenue"

            return json.dumps({
                "action": "skill_call",
                "skill": skill,
                "input": skill_input,
            })

        # Step 2+ — wrap up with the last observation
        last_observation = ""
        for m in reversed(messages):
            if m.get("role") == "user" and m["content"].startswith("Observation:"):
                last_observation = m["content"][len("Observation:"):].strip()
                break

        return json.dumps({
            "action": "done",
            "output": f"Task complete. Result: {last_observation[:500]}",
        })


# ── OpenAI Provider ───────────────────────────────────────────────────────────

class OpenAIProvider:
    name = "openai"

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.api_key = os.environ["OPENAI_API_KEY"]

    def think(self, system_prompt: str, messages: list[dict]) -> str:
        import httpx
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "response_format": {"type": "json_object"},
            "temperature": 0,
        }
        try:
            resp = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
                timeout=30.0,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"OpenAI API error {exc.response.status_code}: {exc.response.text}") from exc
        except Exception as exc:
            raise RuntimeError(f"OpenAI API call failed: {exc}") from exc


# ── Ollama Provider ───────────────────────────────────────────────────────────

class OllamaProvider:
    name = "ollama"

    def __init__(self, model: str = "llama3"):
        self.model = os.getenv("OLLAMA_MODEL", model)
        self.base_url = os.environ["OLLAMA_BASE_URL"].rstrip("/")

    def think(self, system_prompt: str, messages: list[dict]) -> str:
        import httpx
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "stream": False,
            "format": "json",
        }
        try:
            resp = httpx.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=60.0,
            )
            resp.raise_for_status()
            return resp.json()["message"]["content"]
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"Ollama API error {exc.response.status_code}: {exc.response.text}") from exc
        except Exception as exc:
            raise RuntimeError(f"Ollama API call failed: {exc}") from exc


# ── Provider selection ────────────────────────────────────────────────────────

def get_provider() -> PlaceholderProvider | OpenAIProvider | OllamaProvider:
    if os.getenv("OPENAI_API_KEY"):
        logger.info("AI provider: OpenAI (gpt-4o-mini)")
        return OpenAIProvider()
    if os.getenv("OLLAMA_BASE_URL"):
        logger.info("AI provider: Ollama (%s)", os.getenv("OLLAMA_MODEL", "llama3"))
        return OllamaProvider()
    logger.info("AI provider: Placeholder (scripted, no API key required)")
    return PlaceholderProvider()
