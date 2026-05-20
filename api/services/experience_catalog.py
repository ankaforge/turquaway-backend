from __future__ import annotations

import json
from typing import Any, Dict, List

from api.services.openai_client import OpenAIJsonClient


class ExperienceCatalogService:
    def __init__(self, client: OpenAIJsonClient):
        self.client = client

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
        prompt = f"""
You are a local travel operations researcher.
Build a practical experience catalog for a traveler.

City: {city}
Allowed zone: {zone}
Budget: {budget}
Selected activities: {', '.join(activities)}
Response language: {language}

Hard constraints:
- All items must be in the allowed zone or immediate nearby area (max short transfer).
- Prioritize traveler-safe and highly-reviewed places.
- Restaurants and cafes should target rating >= 4.0 when possible.
- Output must include:
  - restaurants_4plus
  - cafes_bistros_4plus
  - yacht_tours
  - diving_tours
  - archaeology_day_trips
  - calm_beach_coves
- If some category cannot be found reliably, return an empty list for that category.
- Keep suggestions realistic for an economy budget.

Return strict JSON object:
{{
  "restaurants_4plus": [{{"name":"string","area":"string","rating":"4.2","reason":"string"}}],
  "cafes_bistros_4plus": [{{"name":"string","area":"string","rating":"4.3","reason":"string"}}],
  "yacht_tours": [{{"name":"string","area":"string","price_hint":"string","reason":"string"}}],
  "diving_tours": [{{"name":"string","area":"string","price_hint":"string","reason":"string"}}],
  "archaeology_day_trips": [{{"name":"string","area":"string","transfer_hint":"string","reason":"string"}}],
  "calm_beach_coves": [{{"name":"string","area":"string","access":"string","reason":"string"}}]
}}
""".strip()

        payload = self.client.chat_json(prompt=prompt, temperature=0.3)
        return {
            "restaurants_4plus": [x for x in (payload.get("restaurants_4plus") or []) if isinstance(x, dict)][:8],
            "cafes_bistros_4plus": [x for x in (payload.get("cafes_bistros_4plus") or []) if isinstance(x, dict)][:8],
            "yacht_tours": [x for x in (payload.get("yacht_tours") or []) if isinstance(x, dict)][:8],
            "diving_tours": [x for x in (payload.get("diving_tours") or []) if isinstance(x, dict)][:8],
            "archaeology_day_trips": [x for x in (payload.get("archaeology_day_trips") or []) if isinstance(x, dict)][:8],
            "calm_beach_coves": [x for x in (payload.get("calm_beach_coves") or []) if isinstance(x, dict)][:8],
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
