import json
import os
import re
import time
from typing import Any, Dict

import httpx


class OpenAIJsonClient:
    def __init__(self, model_name: str = "gpt-4o"):
        api_key = os.getenv("CHATGPT_API_KEY")
        if not api_key:
            raise ValueError("CHATGPT_API_KEY is not set in environment variables.")

        self.api_key = api_key
        self.model_name = os.getenv("OPENAI_MODEL", model_name)
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    def extract_json(self, content: str) -> Dict[str, Any]:
        text = (content or "").strip()
        if not text:
            raise ValueError("OpenAI response content is empty.")

        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\\n", "", text)
            text = re.sub(r"\\n```$", "", text)

        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"OpenAI response is not valid JSON: {text}") from exc

    def chat_json(self, prompt: str, temperature: float = 0.4, max_retries: int | None = None) -> Dict[str, Any]:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": "Return valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
        }

        timeout_seconds = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "12"))
        retry_count = int(os.getenv("OPENAI_MAX_RETRIES", "1")) if max_retries is None else max_retries
        max_retries = max(1, retry_count)

        backoff_seconds = 0.8
        last_error: Exception | None = None

        for attempt in range(max_retries):
            try:
                with httpx.Client(timeout=timeout_seconds) as client:
                    resp = client.post(url, headers=headers, json=payload)

                if resp.status_code >= 400:
                    body = resp.text
                    transient = resp.status_code in {429, 500, 502, 503, 504}
                    if transient and attempt < max_retries - 1:
                        time.sleep(backoff_seconds)
                        backoff_seconds *= 2
                        continue
                    raise ValueError(f"OpenAI API error {resp.status_code}: {body}")

                data = resp.json()
                choices = data.get("choices") or []
                if not choices:
                    raise ValueError("OpenAI response has no choices.")

                message = choices[0].get("message") or {}
                content = message.get("content")
                if not isinstance(content, str):
                    raise ValueError("OpenAI message content is missing or not a string.")

                return self.extract_json(content)

            except Exception as exc:
                last_error = exc
                if attempt < max_retries - 1:
                    time.sleep(backoff_seconds)
                    backoff_seconds *= 2
                    continue
                raise

        raise ValueError(f"OpenAI request failed after retries: {last_error}")
