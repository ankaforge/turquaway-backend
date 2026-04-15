import json
import os
import re
import time
from typing import Any, Dict, List, Tuple
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

    def _parse_time_to_minutes(self, value: str) -> int | None:
        text = str(value or "").strip()
        if not text:
            return None

        match = re.match(r"^(\d{1,2}):(\d{2})$", text)
        if not match:
            return None

        hour = int(match.group(1))
        minute = int(match.group(2))
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            return None
        return hour * 60 + minute

    def _is_turkish(self, language: str) -> bool:
        return str(language or "en").lower().startswith("tr")

    def _minutes_to_time(self, minutes: int) -> str:
        total = max(0, min(23 * 60 + 59, int(minutes)))
        return f"{total // 60:02d}:{total % 60:02d}"

    def _is_far_evening_activity(self, title: str, notes: str, minutes: int | None) -> bool:
        if minutes is None or minutes < 18 * 60:
            return False

        text = f"{title} {notes}".lower()
        far_keywords = [
            "selale",
            "şelale",
            "kanyon",
            "waterfall",
            "national park",
            "milli park",
            "plateau",
            "yayla",
            "outskirts",
            "uzak",
        ]
        return any(keyword in text for keyword in far_keywords)

    def _near_hotel_evening_item(self, city: str, language: str, minutes: int) -> Dict[str, str]:
        if self._is_turkish(language):
            title = f"{city} Otel Cevresi Aksam Kahve ve Yuruyus"
            notes = "Uzak rota yerine otele yakin, guvenli ve dinlendirici aksam programi."
        else:
            title = f"{city} Near-Hotel Evening Coffee and Stroll"
            notes = "Replacing far commute with a nearby and relaxed evening option."

        return {
            "time": self._minutes_to_time(minutes),
            "type": "break",
            "title": title,
            "notes": notes,
        }

    def _normalize_day_timeline(
        self,
        day: Dict[str, Any],
        city: str,
        language: str,
        is_first_day: bool,
        is_last_day: bool,
        min_items: int,
    ) -> None:
        timeline = day.get("timeline") or []
        if not isinstance(timeline, list):
            timeline = []

        valid_items: List[Dict[str, Any]] = []
        for raw in timeline:
            if not isinstance(raw, dict):
                continue
            raw_time = str(raw.get("time") or "").strip() or "10:00"
            minutes = self._parse_time_to_minutes(raw_time)
            if minutes is None:
                minutes = 10 * 60
            raw["time"] = self._minutes_to_time(minutes)

            if self._is_far_evening_activity(str(raw.get("title") or ""), str(raw.get("notes") or ""), minutes):
                valid_items.append(self._near_hotel_evening_item(city=city, language=language, minutes=minutes))
                continue

            valid_items.append(raw)

        valid_items.sort(key=lambda item: self._parse_time_to_minutes(str(item.get("time") or "")) or 0)

        check_in_time = 14 * 60
        check_out_time = 12 * 60
        is_tr = self._is_turkish(language)

        if is_first_day:
            filtered: List[Dict[str, Any]] = []
            for item in valid_items:
                title = str(item.get("title") or "").lower()
                typ = str(item.get("type") or "").lower()
                minutes = self._parse_time_to_minutes(str(item.get("time") or "")) or 0
                is_check_in = "check-in" in title or "check in" in title or typ == "checkin"
                if minutes < check_in_time and not is_check_in:
                    continue
                filtered.append(item)
            valid_items = filtered

            has_checkin = any(
                ("check-in" in str(item.get("title") or "").lower())
                or ("check in" in str(item.get("title") or "").lower())
                or (str(item.get("type") or "").lower() == "checkin")
                for item in valid_items
            )
            if not has_checkin:
                valid_items.insert(
                    0,
                    {
                        "time": "14:00",
                        "type": "checkin",
                        "title": "Otele Giris" if is_tr else "Hotel Check-in",
                        "notes": "Aktivite oncesi otele yerlesme." if is_tr else "Arrival and room settling before activities.",
                    },
                )

        if is_last_day:
            filtered = []
            has_checkout = False
            for item in valid_items:
                title = str(item.get("title") or "").lower()
                typ = str(item.get("type") or "").lower()
                minutes = self._parse_time_to_minutes(str(item.get("time") or "")) or 0
                is_checkout = "check-out" in title or "check out" in title or typ == "checkout"
                if is_checkout:
                    item["time"] = "12:00"
                    has_checkout = True
                    filtered.append(item)
                    continue
                if minutes > check_out_time:
                    continue
                filtered.append(item)

            if not has_checkout:
                filtered.append(
                    {
                        "time": "12:00",
                        "type": "checkout",
                        "title": "Otelden Cikis" if is_tr else "Hotel Check-out",
                        "notes": "Cikis islemleri ve ayrilis." if is_tr else "Check-out and departure.",
                    }
                )

            valid_items = sorted(filtered, key=lambda item: self._parse_time_to_minutes(str(item.get("time") or "")) or 0)

        # Add missing core breaks to keep the plan realistic and paced.
        if is_tr:
            mandatory_breaks: List[Tuple[int, str, str, str]] = [
                (10 * 60 + 30, "break", "Kahve Molasi", "Mevcut rotaya yakin kisa kahve/cay molasi."),
                (13 * 60, "meal", "Ogle Yemegi", "Yerel lezzetlerle oturarak dinlenmeli ogle arasi."),
                (16 * 60 + 30, "rest", "Dinlenme Zamani", "Yorgunlugu azaltmak icin otel veya yakinda dinlenme araligi."),
            ]
        else:
            mandatory_breaks = [
                (10 * 60 + 30, "break", "Coffee Break", "Short coffee/tea break near current route."),
                (13 * 60, "meal", "Lunch", "Local lunch break with seated rest."),
                (16 * 60 + 30, "rest", "Rest Time", "Hotel or nearby resting window to avoid fatigue."),
            ]

        for break_minutes, break_type, break_title, break_notes in mandatory_breaks:
            exists = any(
                abs((self._parse_time_to_minutes(str(item.get("time") or "")) or 0) - break_minutes) <= 60
                and any(
                    token in f"{str(item.get('title') or '').lower()} {str(item.get('type') or '').lower()}"
                    for token in ["coffee", "kahve", "meal", "lunch", "dinner", "food", "rest", "mola", "dinlen"]
                )
                for item in valid_items
            )
            if exists:
                continue

            if is_first_day and break_minutes < check_in_time:
                continue
            if is_last_day and break_minutes > check_out_time:
                continue

            valid_items.append(
                {
                    "time": self._minutes_to_time(break_minutes),
                    "type": break_type,
                    "title": break_title,
                    "notes": break_notes,
                }
            )

        valid_items = sorted(valid_items, key=lambda item: self._parse_time_to_minutes(str(item.get("time") or "")) or 0)

        # Ensure enough density so a full day does not end up with only 1-2 entries.
        filler_cursor = 18 * 60 if not is_last_day else 10 * 60
        while len(valid_items) < min_items:
            valid_items.append(
                {
                    "time": self._minutes_to_time(filler_cursor),
                    "type": "activity",
                    "title": f"{city} Yakindaki Kesif Yuruyusu" if is_tr else f"{city} Nearby Discovery Walk",
                    "notes": "Dusuk transferli, otele yakin yerel aktivite."
                    if is_tr
                    else "Low-transfer local activity close to hotel area.",
                }
            )
            filler_cursor += 90
            if is_last_day and filler_cursor >= 12 * 60:
                filler_cursor = 11 * 60
            if not is_last_day and filler_cursor >= 22 * 60:
                filler_cursor = 21 * 60

        day["timeline"] = sorted(valid_items, key=lambda item: self._parse_time_to_minutes(str(item.get("time") or "")) or 0)

    def _enforce_plan_variation_and_balance(
        self,
        options: List[Dict[str, Any]],
        city: str,
        activities: List[str],
        language: str,
    ) -> List[Dict[str, Any]]:
        placeholder_pattern = re.compile(r"(kesif\s*rotasi|day\s*\d+\s*activity|activity\s*\d+)", re.IGNORECASE)
        is_tr = self._is_turkish(language)
        activity_pool = [a.replace("_", " ").strip().title() for a in activities if str(a).strip()]
        if not activity_pool:
            if is_tr:
                activity_pool = [f"{city} Sehir Turu", f"{city} Yerel Lezzet Deneyimi", f"{city} Sahil Keyfi"]
            else:
                activity_pool = [f"{city} City Walk", f"{city} Local Food Experience", f"{city} Waterfront Relaxation"]

        for option_idx, option in enumerate(options):
            if not isinstance(option, dict):
                continue

            days = option.get("days") or []
            if not isinstance(days, list):
                option["days"] = []
                days = option["days"]

            tempo = "high" if option_idx == 0 else "calm"
            if not option.get("title"):
                if is_tr:
                    option["title"] = f"{city} {'Yuksek Tempolu Kesif' if tempo == 'high' else 'Sakin ve Dengeli Deneyim'}"
                else:
                    option["title"] = f"{city} {'High Tempo Discovery' if tempo == 'high' else 'Calm & Relaxed Experience'}"

            if not option.get("gemini_recommendation") and not option.get("summary"):
                day_count = len(days)
                if tempo == "high":
                    option["summary"] = (
                        f"{city} icin {day_count} gunluk kesif odakli, enerjik plan."
                        if is_tr
                        else f"{day_count}-day energetic exploration-focused plan for {city}."
                    )
                else:
                    option["summary"] = (
                        f"{city} icin {day_count} gunluk sakin, dinlenme dengeli plan."
                        if is_tr
                        else f"{day_count}-day calm and rest-balanced plan for {city}."
                    )

            min_items = 5 if tempo == "high" else 4
            for day_idx, day in enumerate(days):
                if not isinstance(day, dict):
                    continue

                self._normalize_day_timeline(
                    day=day,
                    city=city,
                    language=language,
                    is_first_day=day_idx == 0,
                    is_last_day=day_idx == len(days) - 1,
                    min_items=min_items,
                )

                timeline = day.get("timeline") or []
                for item_idx, item in enumerate(timeline):
                    if not isinstance(item, dict):
                        continue
                    title = str(item.get("title") or "").strip()
                    if not title or placeholder_pattern.search(title):
                        fallback_title = activity_pool[item_idx % len(activity_pool)]
                        item["title"] = f"{city} {fallback_title}"

        if len(options) >= 2:
            first = options[0]
            second = options[1]
            first_title = str(first.get("title") or "").strip()
            second_title = str(second.get("title") or "").strip()
            if first_title.lower() == second_title.lower():
                if is_tr:
                    first["title"] = f"{city} Yuksek Tempolu Kesif"
                    second["title"] = f"{city} Sakin ve Dengeli Deneyim"
                else:
                    first["title"] = f"{city} High Tempo Discovery"
                    second["title"] = f"{city} Calm & Relaxed Experience"

        return options

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
- Option A must be "High tempo discovery" with more exploration.
- Option B must be "Calm & relaxed" with lower tempo and longer rests.
- The two options must be clearly different in rhythm, route density and daily flow.
- Each option must include: plan_id, title, gemini_recommendation or summary, days, estimated_total, currency.
- Day 1 should include check-in around 14:00.
- Final day should include check-out around 12:00.
- Do not schedule any activity before check-in on day 1.
- Do not schedule any activity after check-out on final day.
- For trips >=3 days, keep day 1 and final day lighter.
- Each full day should include at least 4-6 timeline items.
- Balance explore + food + coffee/tea break + rest windows. Do not chain only back-to-back activities.
- Include explicit meal and break entries (coffee/tea, lunch, and rest).
- timeline.title must be real user-facing activity names for {city}.
- Never use placeholders like "Kesif Rotasi 1", "Day 1 Activity", or "Activity 1".
- Respect destination geography and transfer realism:
    - Prefer nearby venues around hotel and same district/cluster.
    - Avoid suggesting far-out locations late evening (after 18:00).
    - Evening entries should favor near-hotel cafes, photo walks, tea/coffee, nightlife in close zones.
    - If city transit is known to be strong (e.g., Istanbul), cross-district moves are allowed but still avoid inefficient zig-zag routes.
- Use hotel context to anchor the route:
    - Infer hotel neighborhood from hotel name when possible.
    - Keep consecutive activities geographically coherent.

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

        return self._enforce_plan_variation_and_balance(
            options=options,
            city=city,
            activities=activities,
            language=language,
        )


def error_response(code: str, detail: str, status_code: int, fields: Dict[str, Any] | None = None) -> Response:
    payload = {
        "code": code,
        "detail": detail,
        "fields": fields or {},
        "trace_id": str(uuid4()),
    }
    return Response(payload, status=status_code)
