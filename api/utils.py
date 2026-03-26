import json
import os
from typing import Any, Dict, List, Union

from google import genai
from google.genai import types


class GeminiService:
    """Service wrapper for Gemini API calls with strict JSON responses."""

    def __init__(self, model_name: str = 'gemini-2.0-flash'):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError('GEMINI_API_KEY is not set in environment variables.')

        self.model_name = os.getenv('GEMINI_MODEL', model_name)
        self.client = genai.Client(api_key=api_key)
        self.generation_config = types.GenerateContentConfig(
            response_mime_type='application/json'
        )

    def _clean_json_text(self, raw_text: str) -> str:
        text = raw_text.strip()
        if text.startswith('```'):
            lines = text.splitlines()
            if lines and lines[0].startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            text = '\n'.join(lines).strip()
        return text

    def _parse_json(self, response: Any) -> Union[Dict[str, Any], List[Any]]:
        raw_text = getattr(response, 'text', '') or ''
        if not raw_text:
            raise ValueError('Gemini response did not contain text content.')

        cleaned = self._clean_json_text(raw_text)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError(f'Gemini response is not valid JSON: {cleaned}') from exc

    def _generate_json_content(self, prompt: str) -> Union[Dict[str, Any], List[Any]]:
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=self.generation_config,
        )
        return self._parse_json(response)

    def get_city_suggestions(self, budget: str, activities: List[str]) -> List[Dict[str, str]]:
        """Return 3-5 city suggestions as a clean JSON list."""
        prompt = f"""
You are a travel planning assistant.
Suggest between 3 and 5 cities based on the provided budget and activities.

Budget: {budget}
Activities: {activities}

Return only valid JSON array (no markdown), in this exact format:
[
  {{"city": "string", "country": "string", "reason": "string"}}
]
""".strip()

        data = self._generate_json_content(prompt)

        if not isinstance(data, list):
            raise ValueError('Expected a JSON list for city suggestions.')

        normalized: List[Dict[str, str]] = []
        for item in data:
            if isinstance(item, dict):
                normalized.append(
                    {
                        'city': str(item.get('city', '')).strip(),
                        'country': str(item.get('country', '')).strip(),
                        'reason': str(item.get('reason', '')).strip(),
                    }
                )

        if not (3 <= len(normalized) <= 5):
            raise ValueError('Gemini should return between 3 and 5 city suggestions.')

        return normalized

    def create_detailed_plan(
        self,
        city: str,
        dates: Dict[str, str],
        guests: int,
        budget: str,
        activities: List[str],
    ) -> Dict[str, Any]:
        """Return a detailed travel plan JSON with itinerary, hotel, and food suggestions."""
        prompt = f"""
You are an expert travel planner.
Create a comprehensive travel plan in JSON for the following details:

City: {city}
Dates: {dates}
Guests: {guests}
Budget: {budget}
Activities: {activities}

The JSON must include at minimum these keys:
- city
- travel_window
- budget_type
- guests
- daily_itinerary (array of daily plans)
- hotel_recommendations (array)
- food_recommendations (array)
- transport_tips (array)
- estimated_cost_breakdown (object)
- important_notes (array)

For daily_itinerary, include morning/afternoon/evening suggestions.
Return only valid JSON object (no markdown, no explanations).
""".strip()

        data = self._generate_json_content(prompt)

        if not isinstance(data, dict):
            raise ValueError('Expected a JSON object for the detailed travel plan.')

        return data