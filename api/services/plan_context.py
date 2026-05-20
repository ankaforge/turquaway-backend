import json
from typing import Any, Dict, List

from api.services.openai_client import OpenAIJsonClient


class PlanContextService:
    def __init__(self, client: OpenAIJsonClient):
        self.client = client

    def language_code(self, language: str) -> str:
        code = str(language or "en").strip().lower()
        if code.startswith("tr"):
            return "tr"
        if code.startswith("ru"):
            return "ru"
        if code.startswith("ar"):
            return "ar"
        return "en"

    def is_turkish(self, language: str) -> bool:
        return self.language_code(language) == "tr"

    def localized_text(self, language: str, key: str, city: str = "") -> str:
        code = self.language_code(language)
        texts = {
            "tr": {
                "near_hotel_evening_title": f"{city} Otel Cevresi Aksam Kahve ve Yuruyus",
                "near_hotel_evening_notes": "Uzak rota yerine otele yakin, guvenli ve dinlendirici aksam programi.",
                "checkin_title": "Otele Giris",
                "checkin_notes": "Aktivite oncesi otele yerlesme.",
                "checkout_title": "Otelden Cikis",
                "checkout_notes": "Cikis islemleri ve ayrilis.",
                "coffee_break_title": "Kahve Molasi",
                "coffee_break_notes": "Mevcut rotaya yakin kisa kahve/cay molasi.",
                "lunch_title": "Ogle Yemegi",
                "lunch_notes": "Yerel lezzetlerle oturarak dinlenmeli ogle arasi.",
                "rest_title": "Dinlenme Zamani",
                "rest_notes": "Yorgunlugu azaltmak icin otel veya yakinda dinlenme araligi.",
                "nearby_walk_title": f"{city} Yakindaki Kesif Yuruyusu",
                "nearby_walk_notes": "Dusuk transferli, otele yakin yerel aktivite.",
            },
            "en": {
                "near_hotel_evening_title": f"{city} Near-Hotel Evening Coffee and Stroll",
                "near_hotel_evening_notes": "Replacing a long commute with a nearby and relaxed evening option.",
                "checkin_title": "Hotel Check-in",
                "checkin_notes": "Arrival and room settling before activities.",
                "checkout_title": "Hotel Check-out",
                "checkout_notes": "Check-out and departure.",
                "coffee_break_title": "Coffee Break",
                "coffee_break_notes": "Short coffee or tea break near the current route.",
                "lunch_title": "Lunch",
                "lunch_notes": "A seated local lunch break with time to rest.",
                "rest_title": "Rest Time",
                "rest_notes": "Hotel or nearby resting window to avoid fatigue.",
                "nearby_walk_title": f"{city} Nearby Discovery Walk",
                "nearby_walk_notes": "A low-transfer local activity close to the hotel area.",
            },
            "ru": {
                "near_hotel_evening_title": f"{city} Vecherniy Kofe i Progulka Ryadom s Otelem",
                "near_hotel_evening_notes": "Vmesto dalekoy poezdki predlagaetsya blizhniy i spokoynyy vecherniy variant.",
                "checkin_title": "Zaselenie v Otel",
                "checkin_notes": "Pribytie i razmeshchenie pered aktivnostyami.",
                "checkout_title": "Vyezd iz Otelya",
                "checkout_notes": "Oformlenie vyezda i otpravlenie.",
                "coffee_break_title": "Kofe-Pauza",
                "coffee_break_notes": "Korotkiy kofe ili chai ryadom s marshrutom.",
                "lunch_title": "Obed",
                "lunch_notes": "Spokoynyy obed s mestnoy kuzhney i otdykhom.",
                "rest_title": "Vremya dlya Otdykha",
                "rest_notes": "Pereryv v otele ili poblizosti, chtoby ne pereutomlyatsya.",
                "nearby_walk_title": f"{city} Progulka po Okrestnostyam",
                "nearby_walk_notes": "Spokoynaya lokalnaya aktivnost nedaleko ot otelya.",
            },
            "ar": {
                "near_hotel_evening_title": f"{city} Qahwa Masa iya wa Nuzha Qarib Min Al Funduq",
                "near_hotel_evening_notes": "Badalan min intiqal baid, tam ikhtiyar khiyar masa i hadi wa qarib.",
                "checkin_title": "Tasjeel Al Dukhool Ila Al Funduq",
                "checkin_notes": "Al wusool wa al istiqrar qabl al anshita.",
                "checkout_title": "Tasjeel Al Khurooj Min Al Funduq",
                "checkout_notes": "Ijraat al khurooj wa al mughadara.",
                "coffee_break_title": "Istirahat Qahwa",
                "coffee_break_notes": "Istirahat qasira lilqahwa aw al shay qarib min al masar.",
                "lunch_title": "Ghadaa",
                "lunch_notes": "Waqfat ghadaa mahalli ma jalasat raaha.",
                "rest_title": "Waqt Lilraaha",
                "rest_notes": "Fatra raaha fi al funduq aw fi makan qarib lijanub al irhaq.",
                "nearby_walk_title": f"{city} Jawla Istikshaf Qariba",
                "nearby_walk_notes": "Nashat mahalli qarib min al funduq wa bidun tanqul tawil.",
            },
        }
        return texts.get(code, texts["en"]).get(key, texts["en"].get(key, ""))

    def build_local_experience_context(
        self,
        city: str,
        hotel_name: str,
        activities: List[str],
        language: str = "en",
        selected_tours: List[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        if not str(hotel_name or "").strip():
            return {
                "hotel_area": "",
                "must_try_foods": [],
                "nearby_places": [],
                "photo_spots": [],
                "avoid_duplicates": [],
            }

        selected_tours = selected_tours or []
        tour_lines = []
        for tour in selected_tours:
            title = str(tour.get("title") or "").strip()
            if not title:
                continue
            line = title
            if tour.get("session_date"):
                line += f" on {tour['session_date']}"
            tour_lines.append(line)

        prompt = f"""
You are a local travel concierge building neighborhood-aware trip context.
Infer the likely hotel area from the hotel name and city when possible.
Do not invent exact street addresses, phone numbers, coordinates, or opening hours.
Use general knowledge and provide practical, itinerary-friendly recommendations.

City: {city}
Hotel name: {hotel_name}
Preferred activities: {', '.join(activities)}
Response language: {language}
Already booked tours or reserved experiences: {json.dumps(tour_lines, ensure_ascii=False)}

Requirements:
- All text values must be written in the requested response language.
- Focus on suggestions plausibly close to the hotel area or the same district cluster.
- Include local foods the traveler should try and a suitable venue or area for each.
- Include nearby places worth visiting.
- Include photo spots.
- Avoid duplicates with already booked tours and avoid closely overlapping recommendations.
- If a booked tour likely already covers ruins, an ancient city, a boat trip, a museum block, or a canyon, do not recommend the same attraction again.
- Prefer human-friendly, itinerary-usable wording.

Return strict JSON object:
{{
  "hotel_area": "string",
  "must_try_foods": [
    {{"dish": "string", "venue": "string", "notes": "string"}}
  ],
  "nearby_places": [
    {{"name": "string", "why_visit": "string", "best_for": "string"}}
  ],
  "photo_spots": [
    {{"name": "string", "best_time": "string", "notes": "string"}}
  ],
  "avoid_duplicates": ["string"]
}}
""".strip()

        payload = self.client.chat_json(prompt=prompt, temperature=0.3)
        return {
            "hotel_area": str(payload.get("hotel_area") or "").strip(),
            "must_try_foods": [
                item for item in (payload.get("must_try_foods") or [])
                if isinstance(item, dict) and str(item.get("dish") or "").strip()
            ][:6],
            "nearby_places": [
                item for item in (payload.get("nearby_places") or [])
                if isinstance(item, dict) and str(item.get("name") or "").strip()
            ][:8],
            "photo_spots": [
                item for item in (payload.get("photo_spots") or [])
                if isinstance(item, dict) and str(item.get("name") or "").strip()
            ][:6],
            "avoid_duplicates": [
                str(item).strip() for item in (payload.get("avoid_duplicates") or []) if str(item).strip()
            ][:10],
        }
