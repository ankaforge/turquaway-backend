import json
from typing import Any, Dict, List

from api.services.openai_client import OpenAIJsonClient


class RecommenderService:
    def __init__(self, client: OpenAIJsonClient):
        self.client = client

    def normalize_city_suggestions(self, data: Any, allowed_destinations: List[str]) -> List[Dict[str, str]]:
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

Your task is to suggest EXACTLY 3 destinations in Turkey based on the user's preferences.

STRICT RULES:
You MUST choose ONLY from the provided allowed destination list.
You MUST return exactly 3 destinations (no more, no less).
Each destination MUST clearly match the user's preferences.

CRITICAL GEOGRAPHY VALIDATION:
Verify that each destination geographically supports the requested activities based on real-world knowledge.
NEVER suggest landlocked cities for sea-based activities
NEVER suggest hot coastal destinations for winter sports, unless there is a well known ski resort nearby.
Avoid contradictory matches between climate, geography and activities.

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

        payload = self.client.chat_json(prompt=prompt, temperature=0.3)
        return self.normalize_city_suggestions(payload.get("items", []), allowed_destinations)

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

        payload = self.client.chat_json(prompt=prompt, temperature=0.2)
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

        payload = self.client.chat_json(prompt=prompt, temperature=0.2)
        items = payload.get("items", [])
        ranked: List[str] = []
        for item in items:
            if isinstance(item, dict):
                item_id = str(item.get("id", "")).strip()
                if item_id:
                    ranked.append(item_id)
        return ranked
