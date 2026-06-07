import json
import re
from typing import Any, Dict, List

from api.services.openai_client import OpenAIJsonClient
from api.services.experience_catalog import ExperienceCatalogService
from api.services.hotel_area import HotelAreaResolver
from api.services.plan_context import PlanContextService
from api.services.plan_postprocess import PlanPostProcessor


class PlanGeneratorService:
    def __init__(self, client: OpenAIJsonClient, context_service: PlanContextService, post_processor: PlanPostProcessor):
        self.client = client
        self.context_service = context_service
        self.post_processor = post_processor
        self.hotel_area_resolver = HotelAreaResolver()
        self.experience_catalog_service = ExperienceCatalogService(client)

    def _catalog_lists_block(self, catalog: Dict[str, Any]) -> str:
        external = catalog.get("external") or {}
        partner = catalog.get("partner_tours") or []

        def fmt(items: List[Dict[str, Any]], key: str = "name", limit: int = 8) -> str:
            lines: List[str] = []
            for item in items[:limit]:
                if not isinstance(item, dict):
                    continue
                value = str(item.get(key) or "").strip()
                area = str(item.get("area") or "").strip()
                rating = str(item.get("rating") or "").strip()
                price_hint = str(item.get("price_hint") or "").strip()
                transfer_hint = str(item.get("transfer_hint") or "").strip()
                extras = ", ".join([x for x in [area, rating, price_hint, transfer_hint] if x])
                if value:
                    lines.append(f"- {value}" + (f" ({extras})" if extras else ""))
            return "\\n".join(lines) if lines else "- none"

        return (
            "Partner Tours:\n"
            + fmt(partner, key="title")
            + "\n\nRestaurants 4+ :\n"
            + fmt(external.get("restaurants_4plus") or [])
            + "\n\nCafes/Bistros 4+ :\n"
            + fmt(external.get("cafes_bistros_4plus") or [])
            + "\n\nYacht Tours:\n"
            + fmt(external.get("yacht_tours") or [])
            + "\n\nDiving Tours:\n"
            + fmt(external.get("diving_tours") or [])
            + "\n\nArchaeology Day Trips:\n"
            + fmt(external.get("archaeology_day_trips") or [])
            + "\n\nCalm Beach Coves:\n"
            + fmt(external.get("calm_beach_coves") or [])
        )

    def _is_generic_title(self, title: str, city: str) -> bool:
        t = (title or "").strip().lower()
        c = (city or "").strip().lower()
        generic_patterns = [
            r"^day\s*\d+\s*activity",
            r"^activity\s*\d+",
            r"kesif\s*rotasi",
            r"serbest\s*zaman",
            r"yerel\s*lezzet\s*duragi",
            r"local\s*food\s*stop",
            r"archaeology$",
            r"diving$",
        ]
        if any(re.search(p, t) for p in generic_patterns):
            return True
        if c and t in {c, f"{c} archaeology", f"{c} diving", f"{c} local food stop"}:
            return True
        return len(t.split()) < 2

    def _validate_quality(self, options: List[Dict[str, Any]], city: str) -> List[str]:
        issues: List[str] = []
        titles: List[str] = []
        notes_blob: List[str] = []
        city_lc = (city or "").strip().lower()
        forbidden_location_terms = [
            "oba",
            "syedra",
            "alanya",
        ]

        for option in options:
            days = option.get("days") or []
            if not isinstance(days, list) or not days:
                issues.append("days list is empty")
                continue
            for day in days:
                timeline = (day or {}).get("timeline") or []
                if len(timeline) < 3:
                    issues.append("a day has fewer than 3 timeline items")
                for item in timeline:
                    if not isinstance(item, dict):
                        issues.append("timeline item is not an object")
                        continue
                    title = str(item.get("title") or "").strip()
                    notes = str(item.get("notes") or "").strip()
                    titles.append(title)
                    notes_blob.append(notes)
                    if self._is_generic_title(title, city):
                        issues.append(f"generic title detected: {title}")

                    text_lc = f"{title} {notes}".lower()
                    for term in forbidden_location_terms:
                        if term in text_lc and term != city_lc:
                            issues.append(f"out-of-city hardcoded location detected: {term}")
                            break

        non_empty_titles = [t for t in titles if t]
        unique_ratio = (len(set(non_empty_titles)) / len(non_empty_titles)) if non_empty_titles else 0.0
        if unique_ratio < 0.6:
            issues.append("too many repeated titles across itinerary")

        joined_notes = " ".join(notes_blob).lower()
        if not re.search(r"source\s*:\s*(partner|external)", joined_notes):
            issues.append("missing Source: Partner/External annotation in notes")
        if not re.search(r"rating\s*[:]?\s*4", joined_notes):
            issues.append("missing 4+ rating signals in notes for food/cafe suggestions")

        deduped: List[str] = []
        for issue in issues:
            if issue not in deduped:
                deduped.append(issue)
        return deduped

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
        hotel_lat: float | None = None,
        hotel_lng: float | None = None,
        selected_tours: List[Dict[str, Any]] | None = None,
        partner_tours: List[Dict[str, Any]] | None = None,
    ) -> List[Dict[str, Any]]:
        hotel_block = f"Accommodation: {hotel_name}" if hotel_name else ""

        area_ctx = self.hotel_area_resolver.resolve(
            city=city,
            hotel_name=hotel_name,
            hotel_lat=hotel_lat,
            hotel_lng=hotel_lng,
        )

        catalog = self.experience_catalog_service.build_catalog(
            city=city,
            zone=area_ctx.zone,
            budget=budget,
            activities=activities,
            language=language,
            partner_tours=partner_tours,
        )

        tour_block = ""
        if selected_tours:
            lines = ["Pre-booked tours (must be integrated into daily schedule):"]
            for tour in selected_tours:
                line = f"- {tour.get('title', 'Tour')}"
                if tour.get("session_date"):
                    line += f" on {tour['session_date']}"
                if tour.get("start_time") and tour.get("end_time"):
                    line += f" from {tour['start_time']} to {tour['end_time']}"
                extras = []
                if tour.get("includes_food"):
                    extras.append("free meals included")
                if tour.get("includes_transfer"):
                    extras.append("hotel pick-up/drop-off included")
                if extras:
                    line += f" ({', '.join(extras)})"
                lines.append(line)
            tour_block = "\\n".join(lines)

        local_context = self.context_service.build_local_experience_context(
            city=city,
            hotel_name=hotel_name,
            activities=activities,
            language=language,
            selected_tours=selected_tours,
            area_zone=area_ctx.zone,
            area_district=area_ctx.district,
        )
        local_context_block = json.dumps(local_context, ensure_ascii=False)
        experience_catalog_block = catalog.get("catalog_json", "{}")
        catalog_lists_block = self._catalog_lists_block(catalog)

        quality_feedback = ""
        options: List[Dict[str, Any]] = []

        for _ in range(3):
            prompt = f"""
You are an expert travel planner.
Generate exactly 2 itinerary options for this trip and return valid JSON only.

City: {city}
Start date: {start_date}
End date: {end_date}
Budget: {budget}
Activities: {', '.join(activities)}
Language: {language}
Family mode: {str(family_mode).lower()}
{hotel_block}
{tour_block}
Local hotel-area context JSON: {local_context_block}
Detected area zone: {area_ctx.zone}
Detected district: {area_ctx.district}
Area confidence: {area_ctx.confidence}
Experience catalog JSON: {experience_catalog_block}
Experience shortlist:\n{catalog_lists_block}
{quality_feedback}

Rules:
- Return exactly 2 options.
- Option A title must imply higher pace; Option B title must imply relaxed pace.
- Keep all user-facing text in requested language.
- Do not produce generic placeholders.
- Use real venue names from shortlist/context where possible.
- Day 1 includes check-in around 14:00; final day includes check-out around 12:00.
- After 18:00, keep activities close to hotel area.
- Keep route geographically coherent and avoid unnecessary zig-zag.
- Include explicit food/coffee breaks and local dishes.
- Restaurant/cafe notes should include rating hints like "Rating: 4.x" where possible.
- Tour/activity notes should include source hints like "Source: Partner" or "Source: External".
- Respect avoid_duplicates from local context.

Output schema:
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
            payload = self.client.chat_json(prompt=prompt, temperature=0.45)
            options = payload.get("items", [])
            if not isinstance(options, list):
                quality_feedback = "\nQuality errors to fix in regeneration: plan items must be a JSON list.\n"
                continue

            if len(options) != 2:
                quality_feedback = f"\nQuality errors to fix in regeneration: Must return exactly 2 plan options, got {len(options)}.\n"
                continue

            issues = self._validate_quality(options=options, city=city)
            if not issues:
                break
            quality_feedback = "\nQuality errors to fix in regeneration:\n- " + "\n- ".join(issues[:8]) + "\n"

        if not isinstance(options, list) or len(options) != 2:
            raise ValueError("Plan generation failed quality gate after retries.")

        return self.post_processor.enforce_plan_variation_and_balance(
            options=options,
            city=city,
            activities=activities,
            language=language,
        )
