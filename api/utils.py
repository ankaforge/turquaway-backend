import json
import os
from typing import Any, Dict, List
from uuid import uuid4

from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from rest_framework.response import Response


class CitySuggestion(BaseModel):
    city: str = Field(description='City name')
    description: str = Field(description='Short reason for recommendation')


class GeminiService:
    """Service wrapper for Gemini API calls with strict structured outputs."""

    def __init__(self, model_name: str = "gemini-2.5-flash"):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in environment variables.")

        self.model_name = os.getenv("GEMINI_MODEL", model_name)
        self.client = genai.Client(api_key=api_key)

    def _normalize_city_suggestions(self, data: Any, allowed_destinations: List[str]) -> List[Dict[str, str]]:
        if not isinstance(data, list):
            raise ValueError("Expected a JSON list for city suggestions.")

        allowed_map = {name.lower(): name for name in allowed_destinations}
        normalized: List[Dict[str, str]] = []
        for item in data:
            if isinstance(item, CitySuggestion):
                city = item.city.strip()
                description = item.description.strip()
            elif isinstance(item, dict):
                city = str(item.get("city", "")).strip()
                description = str(item.get("description", "")).strip()
            else:
                continue

            if not city or not description:
                continue

            key = city.lower()
            if key not in allowed_map:
                continue

            canonical_city = allowed_map[key]
            if canonical_city in [row["city"] for row in normalized]:
                continue
            normalized.append({"city": canonical_city, "description": description})

        # Ensure exactly 3 by filling from allowed destinations when needed.
        if len(normalized) < 3:
            existing = {row["city"] for row in normalized}
            for dest in allowed_destinations:
                if dest in existing:
                    continue
                normalized.append(
                    {
                        "city": dest,
                        "description": "Matches your budget and activity preferences.",
                    }
                )
                existing.add(dest)
                if len(normalized) == 3:
                    break

        if len(normalized) < 3:
            raise ValueError(f"Gemini must return exactly 3 city suggestions, got {len(normalized)}.")

        return normalized[:3]

    def get_city_suggestions(
        self,
        budget: str,
        activities: List[str],
        language: str = "en",
        allowed_destinations: List[str] | None = None,
    ) -> List[Dict[str, str]]:
        allowed_destinations = [item.strip() for item in (allowed_destinations or []) if item and item.strip()]
        if not allowed_destinations:
            raise ValueError("No allowed destinations provided.")

        prompt = f"""
You are a Turkish travel planning assistant.
Suggest exactly 3 destinations in Turkey based on the provided budget and activities.
You MUST choose only from the allowed destination list below.

Budget: {budget}
Activities: {', '.join(activities)}
Response language: {language}
Allowed destinations: {', '.join(allowed_destinations)}

Return only a valid JSON array (no markdown), exactly 3 items, in this format:
[
  {{"city": "string", "description": "string"}}
]
""".strip()

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=list[CitySuggestion],
            temperature=0.7,
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config,
        )

        parsed_data = getattr(response, "parsed", None)
        if parsed_data is not None:
            return self._normalize_city_suggestions(parsed_data, allowed_destinations)

        raw_text = getattr(response, "text", "") or ""
        if not raw_text:
            raise ValueError("Gemini response did not contain text content.")

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Gemini response is not valid JSON: {raw_text}") from exc

        return self._normalize_city_suggestions(data, allowed_destinations)


def error_response(code: str, detail: str, status_code: int, fields: Dict[str, Any] | None = None) -> Response:
    payload = {
        "code": code,
        "detail": detail,
        "fields": fields or {},
        "trace_id": str(uuid4()),
    }
    return Response(payload, status=status_code)
