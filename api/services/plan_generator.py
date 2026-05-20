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
        )
        local_context_block = json.dumps(local_context, ensure_ascii=False)
        experience_catalog_block = catalog.get("catalog_json", "{}")
        catalog_lists_block = self._catalog_lists_block(catalog)

        quality_feedback = ""
        options: List[Dict[str, Any]] = []

        for _ in range(3):
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
Local hotel-area context JSON: {local_context_block}
Detected area zone: {area_ctx.zone}
Detected district: {area_ctx.district}
Area confidence: {area_ctx.confidence}
Experience catalog JSON: {experience_catalog_block}
Experience shortlist:\n{catalog_lists_block}
{quality_feedback}

Rules:
- Return exactly 2 options.
- Option A must be "High tempo discovery" with more exploration.
- Option B must be "Calm & relaxed" with lower tempo and longer rests.
- High tempo: minimum 6-8 activities per full day, includes multiple districts per day.
- Calm: maximum 3-4 activities per day, includes long rest periods (at least 2 hours daily).
- The two options must be clearly different in rhythm, route density and daily flow.
- Each option must include: plan_id, title, gemini_recommendation or summary, days, estimated_total, currency.
- All user-facing text fields must be fully written in the requested language: title, notes, gemini_recommendation, summary, food/place names when applicable.
- Day 1 should include check-in around 14:00.
- Final day should include check-out around 12:00.
- Do not schedule any activity before check-in on day 1.
- Do not schedule any activity after check-out on final day.
- For trips >=3 days, keep day 1 and final day lighter.
- Each full day should include at least 4-6 timeline items.
- Balance explore + food + coffee/tea break + rest windows. Do not chain only back-to-back activities.
- Include explicit meal and break entries (coffee/tea, lunch, and rest).
- For each meal, include a specific venue name when possible.
- Dining and cafe entries must include "Rating: 4.x" in notes where possible.
- Each tour/experience item notes must include "Source: Partner" or "Source: External".
- Avoid repeated titles across days. Prefer unique venue names and varied route composition.
- Mention at least one local dish per day within meal entries.
- timeline.title must be real user-facing activity names for {city}.
- timeline.title must include explicit place/venue names from Experience shortlist where possible.
- Never use placeholders like "Kesif Rotasi 1", "Day 1 Activity", or "Activity 1".
- Use the local hotel-area context.
- You must stay within detected area zone: {area_ctx.zone} unless explicitly marked as a day-trip.
- Any suggestion outside zone must be rejected unless it is in archaeology_day_trips and includes transfer_hint.
- Prioritize places within 1-2 km of the hotel for evening activities.
- Use local_context_block to select nearby cafes, restaurants, and photo spots.
- Use the provided Experience catalog JSON as the primary source list.
- Prefer partner tours first. If partner tours are missing in a category, use external fallback entries from the catalog.
- When multiple options exist, prefer locations with higher popularity or better scenic value.
- Ensure the first and last activities of each day are near the hotel area.
- Integrate must-try dishes and suitable venues into meal entries where it makes sense.
- Use nearby places and photo spots from the local context when building the route.
- Prefer route coherence around the inferred hotel area or same district cluster.
- Do not recommend items listed in avoid_duplicates.
- If a pre-booked tour likely covers a landmark or district, do not recommend the same attraction again unless it is only a brief photo stop clearly different from the reserved experience.
- Respect destination geography and transfer realism:
    - Prefer nearby venues around hotel and same district/cluster.
    - Avoid suggesting far-out locations late evening (after 18:00).
    - Evening entries should favor near-hotel cafes, photo walks, tea/coffee, nightlife in close zones.
    - If city transit is known to be strong (e.g., Istanbul), cross-district moves are allowed but still avoid inefficient zig-zag routes.
    - Group activities by district. Do not switch districts more than 2 times per day.
    - Walking distance between consecutive items should be realistic (<20 min when possible).
- Use hotel context to anchor the route:
    - Infer hotel neighborhood from hotel name when possible.
    - Keep consecutive activities geographically coherent.
- Do not repeat the same attraction across days.
- Add realistic travel time between activities when districts change.
- Return output strictly in valid JSON format.
- Do not include any explanation outside JSON.

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
