from __future__ import annotations

import json
from typing import Any, Dict, List

from api.services.openai_client import OpenAIJsonClient


class ExperienceCatalogService:
    def __init__(self, client: OpenAIJsonClient):
        self.client = client

    def _normalized_activity_keys(self, activities: List[str]) -> List[str]:
        unique: List[str] = []
        for item in activities or []:
            key = str(item or "").strip().lower()
            if key and key not in unique:
                unique.append(key)
        return unique

    def _normalize_partner_tours(self, partner_tours: List[Dict[str, Any]] | None) -> List[Dict[str, Any]]:
        normalized = []
        for item in (partner_tours or []):
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            if not title:
                continue
            normalized.append(
                {
                    "title": title,
                    "category": str(item.get("category") or "general").strip() or "general",
                    "price_level": str(item.get("price_level") or "").strip(),
                    "area": str(item.get("area") or "").strip(),
                    "source": "partner",
                }
            )
        return normalized

    def _external_fallback(
        self,
        city: str,
        zone: str,
        budget: str,
        activities: List[str],
        language: str,
    ) -> Dict[str, Any]:
        activity_keys = self._normalized_activity_keys(activities)
        prompt = f"""
You are a local travel operations researcher.
Build a practical experience catalog for a traveler.

City: {city}
Allowed zone: {zone}
Budget: {budget}
Selected activity keys: {', '.join(activity_keys)}
Response language: {language}
Activity keys JSON: {json.dumps(activity_keys, ensure_ascii=False)}

Hard constraints:
- All items must be in the allowed zone or immediate nearby area (max short transfer).
- Prioritize traveler-safe and highly-reviewed places.
- Restaurants and cafes should target rating >= 4.0 when possible.
- Output must include:
  - restaurants_4plus
  - cafes_bistros_4plus
    - activity_specific_options (object keyed by selected activity keys)
  - calm_beach_coves
- Output must include activity_providers list. For each item include phone and website when known.
- If phone/website cannot be verified, return empty string instead of inventing values.
- If some category cannot be found reliably, return an empty list for that category.
- Keep suggestions realistic for an economy budget.
- activity_specific_options must have an entry for every selected activity key.
- For every selected activity key, prioritize entries with operational provider contact details.

Return strict JSON object:
{{
  "restaurants_4plus": [{{"name":"string","area":"string","rating":"4.2","reason":"string"}}],
  "cafes_bistros_4plus": [{{"name":"string","area":"string","rating":"4.3","reason":"string"}}],
        "activity_specific_options": {{
                "<activity_key>": [{{"name":"string","area":"string","price_hint":"string","transfer_hint":"string","phone":"string","website":"string","reason":"string"}}]
        }},
    "calm_beach_coves": [{{"name":"string","area":"string","access":"string","reason":"string"}}],
    "activity_providers": [
        {{"activity":"string","name":"string","area":"string","phone":"string","website":"string","notes":"string"}}
    ]
}}
""".strip()

        payload = self.client.chat_json(prompt=prompt, temperature=0.3)
        activity_specific_options: Dict[str, Any] = payload.get("activity_specific_options") or {}
        if not isinstance(activity_specific_options, dict):
            activity_specific_options = {}

        normalized_activity_specific_options: Dict[str, List[Dict[str, Any]]] = {}
        for key in activity_keys:
            items = activity_specific_options.get(key) or []
            normalized_activity_specific_options[key] = [x for x in items if isinstance(x, dict)][:8]

        return {
            "restaurants_4plus": [x for x in (payload.get("restaurants_4plus") or []) if isinstance(x, dict)][:8],
            "cafes_bistros_4plus": [x for x in (payload.get("cafes_bistros_4plus") or []) if isinstance(x, dict)][:8],
            "activity_specific_options": normalized_activity_specific_options,
            "calm_beach_coves": [x for x in (payload.get("calm_beach_coves") or []) if isinstance(x, dict)][:8],
            "activity_providers": [x for x in (payload.get("activity_providers") or []) if isinstance(x, dict)][:12],
        }

    def build_catalog(
        self,
        city: str,
        zone: str,
        budget: str,
        activities: List[str],
        language: str,
        partner_tours: List[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        partner = self._normalize_partner_tours(partner_tours)
        external = self._external_fallback(
            city=city,
            zone=zone,
            budget=budget,
            activities=activities,
            language=language,
        )

        return {
            "zone": zone,
            "budget": budget,
            "activities": activities,
            "partner_tours": partner,
            "external": external,
            "has_partner_options": len(partner) > 0,
            "source_policy": "partner_first_external_fallback",
            "catalog_json": json.dumps({"partner_tours": partner, "external": external}, ensure_ascii=False),
        }
