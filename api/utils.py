import json
import os
import re
import time
from typing import Any, Dict, List
from uuid import uuid4

import httpx
from rest_framework.response import Response


class GeminiService:
    """Compatibility service: existing call sites keep using GeminiService name, but provider is OpenAI."""

    def __init__(self, model_name: str = "gpt-4o"):
        api_key = os.getenv("CHATGPT_API_KEY")
        if not api_key:
            raise ValueError("CHATGPT_API_KEY is not set in environment variables.")

        self.api_key = api_key
        self.model_name = os.getenv("OPENAI_MODEL", model_name)
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    def _extract_json(self, content: str) -> Dict[str, Any]:
        text = (content or "").strip()
        if not text:
            raise ValueError("OpenAI response content is empty.")

        # Handle possible markdown code fences.
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\\n", "", text)
            text = re.sub(r"\\n```$", "", text)

        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"OpenAI response is not valid JSON: {text}") from exc

    def _chat_json(self, prompt: str, temperature: float = 0.4, max_retries: int = 3) -> Dict[str, Any]:
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

        backoff_seconds = 0.8
        last_error: Exception | None = None

        for attempt in range(max_retries):
            try:
                with httpx.Client(timeout=45.0) as client:
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

                return self._extract_json(content)

            except Exception as exc:
                last_error = exc
                if attempt < max_retries - 1:
                    time.sleep(backoff_seconds)
                    backoff_seconds *= 2
                    continue
                raise

        raise ValueError(f"OpenAI request failed after retries: {last_error}")

    def _normalize_city_suggestions(self, data: Any, allowed_destinations: List[str]) -> List[Dict[str, str]]:
        if not isinstance(data, list):
            raise ValueError("Expected a JSON list for city suggestions.")

        allowed_map = {name.lower(): name for name in allowed_destinations}
        normalized: List[Dict[str, str]] = []

        for item in data:
            if not isinstance(item, dict):
                continue

            city = str(item.get("city", "")).strip()
            description = str(item.get("description", "")).strip()
            if not city or not description:
                continue

            key = city.lower()
            if key not in allowed_map:
                continue

            canonical_city = allowed_map[key]
            if canonical_city in [row["city"] for row in normalized]:
                continue

            normalized.append({"city": canonical_city, "description": description})

        if len(normalized) < 3:
            existing = {row["city"] for row in normalized}
            for dest in allowed_destinations:
                if dest in existing:
                    continue
                normalized.append(
                    {
                        "city": dest,
                        "description": "Butce ve etkinlik tercihlerinize uygun alternatif rota.",
                    }
                )
                existing.add(dest)
                if len(normalized) == 3:
                    break

        if len(normalized) < 3:
            raise ValueError(f"Must return exactly 3 city suggestions, got {len(normalized)}.")

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
You are an expert Turkish travel planning assistant.
Suggest exactly 3 destinations in Turkey based on user preferences.
You MUST choose only from the allowed destination list.

CRITICAL GEOGRAPHY RULES:
1) Verify destination geography supports requested activities.
2) Do not suggest landlocked cities for swimming/beach/diving/sea.
3) Do not suggest hot coastal cities for skiing/snowboarding unless there is a known ski resort context.
4) Discard contradictory city-activity matches.

Budget: {budget}
Activities: {', '.join(activities)}
Response language: {language}
Allowed destinations: {', '.join(allowed_destinations)}

Return strict JSON object:
{{
  "items": [
    {{"city": "string", "description": "string"}}
  ]
}}
""".strip()

        payload = self._chat_json(prompt=prompt, temperature=0.3)
        return self._normalize_city_suggestions(payload.get("items", []), allowed_destinations)

    def rank_hotels(
        self,
        hotels: List[Dict[str, Any]],
        budget: str,
        activities: List[str],
        language: str = "en",
    ) -> List[str]:
        if not hotels:
            return []

        prompt = f"""
Rank hotel candidates by user preference.
Budget: {budget}
Activities: {', '.join(activities)}
Language: {language}
Candidates JSON: {json.dumps(hotels, ensure_ascii=False)}

Return strict JSON object:
{{
  "items": [
    {{"id": "uuid"}}
  ]
}}
""".strip()

        payload = self._chat_json(prompt=prompt, temperature=0.2)
        items = payload.get("items", [])
        ranked: List[str] = []
        for item in items:
            if isinstance(item, dict):
                item_id = str(item.get("id", "")).strip()
                if item_id:
                    ranked.append(item_id)
        return ranked

    def rank_tours(
        self,
        tours: List[Dict[str, Any]],
        budget: str,
        activities: List[str],
        language: str = "en",
        family_mode: bool = False,
    ) -> List[str]:
        if not tours:
            return []

        prompt = f"""
Rank tour candidates by user preference.
Budget: {budget}
Activities: {', '.join(activities)}
Language: {language}
Family mode: {str(family_mode).lower()}
Candidates JSON: {json.dumps(tours, ensure_ascii=False)}

Return strict JSON object:
{{
  "items": [
    {{"id": "uuid"}}
  ]
}}
""".strip()

        payload = self._chat_json(prompt=prompt, temperature=0.2)
        items = payload.get("items", [])
        ranked: List[str] = []
        for item in items:
            if isinstance(item, dict):
                item_id = str(item.get("id", "")).strip()
                if item_id:
                    ranked.append(item_id)
        return ranked

    def generate_plan_options(
        self,
        city: str,
        start_date: str,
        end_date: str,
        budget: str,
        activities: List[str],
        language: str = "en",
        family_mode: bool = False,
        hotel_name: str = "",
        selected_tours: List[Dict[str, Any]] | None = None,
    ) -> List[Dict[str, Any]]:
        hotel_block = f"Accommodation: {hotel_name}" if hotel_name else ""

        tour_block = ""
        if selected_tours:
            lines = ["Pre-booked tours (must be integrated into daily schedule):"]
            for t in selected_tours:
                line = f"- {t.get('title', 'Tour')}"
                if t.get("session_date"):
                    line += f" on {t['session_date']}"
                if t.get("start_time") and t.get("end_time"):
                    line += f" from {t['start_time']} to {t['end_time']}"
                extras = []
                if t.get("includes_food"):
                    extras.append("free meals included")
                if t.get("includes_transfer"):
                    extras.append("hotel pick-up/drop-off included")
                if extras:
                    line += f" ({', '.join(extras)})"
                lines.append(line)
            tour_block = "\\n".join(lines)

        prompt = f"""
You are an expert travel planner.
Generate exactly 2 plan options for this trip.

City: {city}
Start date: {start_date}
End date: {end_date}
Budget: {budget}
Activities: {', '.join(activities)}
Language: {language}
Family mode: {str(family_mode).lower()}
{hotel_block}
{tour_block}

Rules:
- Return exactly 2 options.
- Each option must include: plan_id, title, gemini_recommendation or summary, days, estimated_total, currency.
- Day 1 should include check-in around 14:00.
- Final day should include check-out around 12:00.
- For trips >=3 days, keep day 1 and final day lighter.
- timeline.title must be real user-facing activity names for {city}.
- Never use placeholders like "Kesif Rotasi 1", "Day 1 Activity", or "Activity 1".

Return strict JSON object:
{{
  "items": [
    {{
      "plan_id": "string",
      "title": "string",
      "gemini_recommendation": "string",
      "summary": "string",
      "days": [
        {{
          "day": 1,
          "timeline": [
            {{"time": "09:00", "type": "activity", "title": "string", "notes": "string"}}
          ]
        }}
      ],
      "estimated_total": 12000,
      "currency": "TRY"
    }}
  ]
}}
""".strip()

        payload = self._chat_json(prompt=prompt, temperature=0.6)
        options = payload.get("items", [])
        if not isinstance(options, list):
            raise ValueError("Plan options payload is not a list.")

        if len(options) != 2:
            raise ValueError(f"Must return exactly 2 plan options, got {len(options)}.")

        placeholder_pattern = re.compile(r"(kesif\\s*rotasi|day\\s*\\d+\\s*activity|activity\\s*\\d+)", re.IGNORECASE)
        activity_pool = [a.replace("_", " ").strip().title() for a in activities if str(a).strip()]
        if not activity_pool:
            activity_pool = [f"{city} Sehir Turu", f"{city} Yerel Lezzet Deneyimi", f"{city} Sahil Keyfi"]

        for option in options:
            if not isinstance(option, dict):
                continue

            if not option.get("gemini_recommendation") and not option.get("summary"):
                day_count = len(option.get("days") or [])
                option["summary"] = f"{city} icin {day_count} gunluk dengeli gezi plani."

            for day in option.get("days") or []:
                timeline = day.get("timeline") or []
                for idx, item in enumerate(timeline):
                    title = str(item.get("title") or "").strip()
                    if not title or placeholder_pattern.search(title):
                        fallback_title = activity_pool[idx % len(activity_pool)]
                        item["title"] = f"{city} {fallback_title}"

        return options


def error_response(code: str, detail: str, status_code: int, fields: Dict[str, Any] | None = None) -> Response:
    payload = {
        "code": code,
        "detail": detail,
        "fields": fields or {},
        "trace_id": str(uuid4()),
    }
    return Response(payload, status=status_code)
