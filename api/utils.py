import json
import os
from typing import Any, Dict, List, Union

from google import genai
from google.genai import types


class GeminiService:
    """Service wrapper for Gemini API calls with strict JSON responses."""

    def __init__(self, model_name: str = 'gemini-2.5-flash'):
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
        """Return exactly 3 city suggestions for Turkey as a JSON list."""
        prompt = f"""
You are a Turkish travel planning assistant.
Suggest exactly 3 cities in Turkey based on the provided budget and activities.

Budget: {budget}
Activities: {', '.join(activities)}

Return only a valid JSON array (no markdown), exactly 3 items, in this format:
[
  {{"city": "string", "country": "Turkey", "reason": "string"}}
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
                        'country': str(item.get('country', 'Turkey')).strip(),
                        'reason': str(item.get('reason', '')).strip(),
                    }
                )

        if len(normalized) != 3:
            raise ValueError('Gemini must return exactly 3 city suggestions.')

        return normalized

    def create_detailed_plan(
        self,
        city: str,
        start_date: str,
        end_date: str,
        adults: int,
        children: int,
        budget: str,
        activities: List[str],
    ) -> Dict[str, Any]:
        """Return a structured itinerary matching the mobile app schema."""
        family_mode = children > 0
        family_note = (
            f'There are {children} child(ren) in the group. '
            'ALL recommendations MUST be family-friendly and safe for children. '
            'NEVER include adult-only venues, nightlife, bars, or age-restricted activities. '
            'Mark adult_only as false for every item. Set family_friendly to true for every item. '
            'Set min_age to 0 unless a specific age restriction genuinely applies (e.g. 7+ for rafting).'
            if family_mode else
            'No children in the group. Adult venues and nightlife are acceptable.'
        )

        prompt = f"""
You are an expert Turkish travel planner.
Create a comprehensive travel itinerary in JSON for the following trip:

City: {city}
Dates: {start_date} to {end_date}
Adults: {adults}, Children: {children}
Budget: {budget}
Activities: {', '.join(activities)}

IMPORTANT — Child Safety Rule:
{family_note}

Return a single JSON object with this EXACT structure (no markdown, no extra keys):
{{
  "city": "{city}",
  "header_image": null,
  "daily_plan": [
    {{
      "day": 1,
      "title": "Day theme title",
      "activities": [
        {{
          "time": "09:00",
          "name": "Activity name",
          "transportation_note": "How to get there",
          "price": "free or estimated price or null",
          "min_age": null,
          "family_friendly": true,
          "adult_only": false
        }}
      ],
      "dining": [
        {{
          "time": "13:00",
          "name": "Restaurant or meal suggestion",
          "price": "estimated price per person",
          "cuisine": "cuisine type"
        }}
      ]
    }}
  ],
  "accommodation": [
    {{
      "name": "Hotel name",
      "area": "Neighbourhood",
      "price": "price per night",
      "family_friendly": true,
      "child_bed_available": true,
      "adult_only": false
    }}
  ]
}}

Generate one day entry per calendar day between {start_date} and {end_date}.
""".strip()

        data = self._generate_json_content(prompt)

        if not isinstance(data, dict):
            raise ValueError('Expected a JSON object for the detailed travel plan.')

        # Post-generation safety filter: strip adult-only items when children present
        if family_mode:
            for day in data.get('daily_plan', []):
                day['activities'] = [
                    a for a in day.get('activities', [])
                    if not a.get('adult_only', False)
                ]
            data['accommodation'] = [
                h for h in data.get('accommodation', [])
                if not h.get('adult_only', False)
            ]

        return data

