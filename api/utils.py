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


class RankedItem(BaseModel):
    id: str = Field(description='UUID of candidate item')


class TimelineItem(BaseModel):
    time: str = Field(description='Time in HH:MM format')
    type: str = Field(description='Type of timeline item')
    title: str = Field(description='Title of timeline item')
    notes: str = Field(description='Short notes')


class PlanDay(BaseModel):
    day: int = Field(description='Day index starting from 1')
    timeline: List[TimelineItem] = Field(description='Timeline items for that day')


class PlanOption(BaseModel):
    plan_id: str = Field(description='Plan identifier')
    title: str = Field(description='Plan title')
    days: List[PlanDay] = Field(description='Daily timeline list')
    estimated_total: int = Field(description='Estimated total cost')
    currency: str = Field(description='Currency code')


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

    def rank_hotels(
        self,
        hotels: List[Dict[str, Any]],
        budget: str,
        activities: List[str],
        language: str = 'en',
    ) -> List[str]:
        if not hotels:
            return []

        candidate_json = json.dumps(hotels, ensure_ascii=False)
        prompt = f"""
You are a travel assistant.
Rank the hotel candidates by best match for the user preferences.

Budget: {budget}
Activities: {', '.join(activities)}
Language: {language}

Candidates JSON:
{candidate_json}

Return only a JSON array with the same hotel IDs in preferred order.
Format:
[
  {{"id": "uuid"}}
]
""".strip()

        config = types.GenerateContentConfig(
            response_mime_type='application/json',
            response_schema=list[RankedItem],
            temperature=0.3,
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config,
        )

        parsed_data = getattr(response, 'parsed', None)
        data = parsed_data if parsed_data is not None else json.loads((getattr(response, 'text', '') or '[]'))
        if not isinstance(data, list):
            return []

        ordered_ids: List[str] = []
        for item in data:
            item_id = item.id if isinstance(item, RankedItem) else str(item.get('id', '')).strip()
            if item_id:
                ordered_ids.append(item_id)
        return ordered_ids

    def rank_tours(
        self,
        tours: List[Dict[str, Any]],
        budget: str,
        activities: List[str],
        language: str = 'en',
        family_mode: bool = False,
    ) -> List[str]:
        if not tours:
            return []

        candidate_json = json.dumps(tours, ensure_ascii=False)
        prompt = f"""
You are a travel assistant.
Rank the tour candidates by best match for the user preferences.

Budget: {budget}
Activities: {', '.join(activities)}
Language: {language}
Family mode: {str(family_mode).lower()}

Candidates JSON:
{candidate_json}

Return only a JSON array with the same tour IDs in preferred order.
Format:
[
  {{"id": "uuid"}}
]
""".strip()

        config = types.GenerateContentConfig(
            response_mime_type='application/json',
            response_schema=list[RankedItem],
            temperature=0.3,
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config,
        )

        parsed_data = getattr(response, 'parsed', None)
        data = parsed_data if parsed_data is not None else json.loads((getattr(response, 'text', '') or '[]'))
        if not isinstance(data, list):
            return []

        ordered_ids: List[str] = []
        for item in data:
            item_id = item.id if isinstance(item, RankedItem) else str(item.get('id', '')).strip()
            if item_id:
                ordered_ids.append(item_id)
        return ordered_ids

    def generate_plan_options(
        self,
        city: str,
        start_date: str,
        end_date: str,
        budget: str,
        activities: List[str],
        language: str = 'en',
        family_mode: bool = False,
    ) -> List[Dict[str, Any]]:
        prompt = f"""
You are a travel planner.
Generate exactly 2 plan options for the given trip.

City: {city}
Start date: {start_date}
End date: {end_date}
Budget: {budget}
Activities: {', '.join(activities)}
Language: {language}
Family mode: {str(family_mode).lower()}

Rules:
- Return exactly 2 options.
- Each option must include plan_id, title, days, estimated_total, currency.
- Each day must include timeline items with time/type/title/notes.
- Keep output concise and realistic.
""".strip()

        config = types.GenerateContentConfig(
            response_mime_type='application/json',
            response_schema=list[PlanOption],
            temperature=0.6,
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config,
        )

        parsed_data = getattr(response, 'parsed', None)
        data = parsed_data if parsed_data is not None else json.loads((getattr(response, 'text', '') or '[]'))
        if not isinstance(data, list):
            raise ValueError('Gemini plan options are not a list.')

        options: List[Dict[str, Any]] = []
        for item in data:
            if isinstance(item, PlanOption):
                options.append(item.model_dump())
            elif isinstance(item, dict):
                options.append(item)

        if len(options) != 2:
            raise ValueError(f'Gemini must return exactly 2 plan options, got {len(options)}.')

        return options


def error_response(code: str, detail: str, status_code: int, fields: Dict[str, Any] | None = None) -> Response:
    payload = {
        "code": code,
        "detail": detail,
        "fields": fields or {},
        "trace_id": str(uuid4()),
    }
    return Response(payload, status=status_code)
