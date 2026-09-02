"""
AlphaGuard AI - AI Provider Abstraction Layer
================================================
Supports openai / anthropic / gemini via AI_PROVIDER env var.
If no AI_API_KEY is configured, the service NEVER crashes - it returns
clearly-labeled deterministic DEMO MODE responses so the whole app keeps
working without any external key.

Agents call `ai_service.complete_json(system_prompt, user_prompt, demo_fallback)`
and always get back a Python dict, whether from a real LLM or from the
deterministic fallback generator supplied by the caller.
"""
import json
import requests
from flask import current_app


class AIService:
    def __init__(self, app=None):
        self.provider = "openai"
        self.api_key = ""
        self.configured = False
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.provider = app.config.get("AI_PROVIDER", "openai")
        self.api_key = app.config.get("AI_API_KEY", "")
        self.configured = bool(self.api_key)

    def complete_json(self, system_prompt, user_prompt, demo_fallback):
        """
        Returns a python dict. demo_fallback is a zero-arg callable that
        produces a deterministic dict when no AI key is configured or the
        call fails for any reason (never crashes the app).
        """
        if not self.configured:
            result = demo_fallback()
            result["_source"] = "DEMO_MODE"
            return result

        try:
            text = self._call_provider(system_prompt, user_prompt)
            cleaned = text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.strip("`")
                cleaned = cleaned.replace("json\n", "", 1) if cleaned.startswith("json\n") else cleaned
            data = json.loads(cleaned)
            data["_source"] = f"AI:{self.provider}"
            return data
        except Exception as e:
            current_app.logger.warning(f"AI provider call failed, using demo fallback: {e}")
            result = demo_fallback()
            result["_source"] = "DEMO_MODE_FALLBACK"
            return result

    def _call_provider(self, system_prompt, user_prompt):
        if self.provider == "openai":
            return self._call_openai(system_prompt, user_prompt)
        elif self.provider == "anthropic":
            return self._call_anthropic(system_prompt, user_prompt)
        elif self.provider == "gemini":
            return self._call_gemini(system_prompt, user_prompt)
        raise ValueError(f"Unsupported AI_PROVIDER: {self.provider}")

    def _call_openai(self, system_prompt, user_prompt):
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.4,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def _call_anthropic(self, system_prompt, user_prompt):
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 1000,
                "system": system_prompt + "\nRespond ONLY with valid JSON, no preamble.",
                "messages": [{"role": "user", "content": user_prompt}],
            },
            timeout=30,
        )
        resp.raise_for_status()
        content = resp.json()["content"]
        return "".join(b.get("text", "") for b in content if b.get("type") == "text")

    def _call_gemini(self, system_prompt, user_prompt):
        for model in ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.5-pro", "gemini-2.5-flash-lite"]:
            try:
                resp = requests.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}",
                    json={
                        "contents": [{"parts": [{"text": system_prompt + "\n\n" + user_prompt}]}],
                        "generationConfig": {"response_mime_type": "application/json"},
                    },
                    timeout=20,
                )
                if resp.status_code == 200:
                    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            except Exception:
                continue
        raise RuntimeError("All Gemini model endpoints failed or were rate-limited.")

    def generate_postmortem_narrative(self, trade_dict, base):
        system = "You are a disciplined trading post-mortem analyst. Respond ONLY with JSON."
        user = (
            f"Trade: {json.dumps(trade_dict)}\nOutcome summary: {json.dumps(base)}\n"
            "Return JSON with keys: what_worked, what_failed, future_recommendation. "
            "Each value should be one concise sentence."
        )

        def fallback():
            from trading.postmortem import _deterministic_narrative
            return _deterministic_narrative(base)

        result = self.complete_json(system, user, fallback)
        return {
            "what_worked": result.get("what_worked", ""),
            "what_failed": result.get("what_failed", ""),
            "future_recommendation": result.get("future_recommendation", ""),
        }


ai_service = AIService()
