import re
from typing import Any, Dict, List, Tuple

from api.services.plan_context import PlanContextService


class PlanPostProcessor:
    def __init__(self, context_service: PlanContextService):
        self.context_service = context_service

    def parse_time_to_minutes(self, value: str) -> int | None:
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

    def minutes_to_time(self, minutes: int) -> str:
        total = max(0, min(23 * 60 + 59, int(minutes)))
        return f"{total // 60:02d}:{total % 60:02d}"

    def is_far_evening_activity(self, title: str, notes: str, minutes: int | None) -> bool:
        if minutes is None or minutes < 18 * 60:
            return False

        text = f"{title} {notes}".lower()
        far_keywords = [
            "selale",
            "selale",
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

    def near_hotel_evening_item(self, city: str, language: str, minutes: int) -> Dict[str, str]:
        return {
            "time": self.minutes_to_time(minutes),
            "type": "break",
            "title": self.context_service.localized_text(language, "near_hotel_evening_title", city=city),
            "notes": self.context_service.localized_text(language, "near_hotel_evening_notes", city=city),
        }

    def normalize_day_timeline(
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
            minutes = self.parse_time_to_minutes(raw_time)
            if minutes is None:
                minutes = 10 * 60
            raw["time"] = self.minutes_to_time(minutes)

            if self.is_far_evening_activity(str(raw.get("title") or ""), str(raw.get("notes") or ""), minutes):
                valid_items.append(self.near_hotel_evening_item(city=city, language=language, minutes=minutes))
                continue

            valid_items.append(raw)

        valid_items.sort(key=lambda item: self.parse_time_to_minutes(str(item.get("time") or "")) or 0)

        check_in_time = 14 * 60
        check_out_time = 12 * 60
        if is_first_day:
            filtered: List[Dict[str, Any]] = []
            for item in valid_items:
                title = str(item.get("title") or "").lower()
                typ = str(item.get("type") or "").lower()
                minutes = self.parse_time_to_minutes(str(item.get("time") or "")) or 0
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
                        "title": self.context_service.localized_text(language, "checkin_title", city=city),
                        "notes": self.context_service.localized_text(language, "checkin_notes", city=city),
                    },
                )

        if is_last_day:
            filtered = []
            has_checkout = False
            for item in valid_items:
                title = str(item.get("title") or "").lower()
                typ = str(item.get("type") or "").lower()
                minutes = self.parse_time_to_minutes(str(item.get("time") or "")) or 0
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
                        "title": self.context_service.localized_text(language, "checkout_title", city=city),
                        "notes": self.context_service.localized_text(language, "checkout_notes", city=city),
                    }
                )

            valid_items = sorted(filtered, key=lambda item: self.parse_time_to_minutes(str(item.get("time") or "")) or 0)

        mandatory_breaks: List[Tuple[int, str, str, str]] = [
            (
                10 * 60 + 30,
                "break",
                self.context_service.localized_text(language, "coffee_break_title", city=city),
                self.context_service.localized_text(language, "coffee_break_notes", city=city),
            ),
            (
                13 * 60,
                "meal",
                self.context_service.localized_text(language, "lunch_title", city=city),
                self.context_service.localized_text(language, "lunch_notes", city=city),
            ),
            (
                16 * 60 + 30,
                "rest",
                self.context_service.localized_text(language, "rest_title", city=city),
                self.context_service.localized_text(language, "rest_notes", city=city),
            ),
        ]

        for break_minutes, break_type, break_title, break_notes in mandatory_breaks:
            exists = any(
                abs((self.parse_time_to_minutes(str(item.get("time") or "")) or 0) - break_minutes) <= 60
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
                    "time": self.minutes_to_time(break_minutes),
                    "type": break_type,
                    "title": break_title,
                    "notes": break_notes,
                }
            )

        valid_items = sorted(valid_items, key=lambda item: self.parse_time_to_minutes(str(item.get("time") or "")) or 0)

        filler_cursor = 18 * 60 if not is_last_day else 10 * 60
        while len(valid_items) < min_items:
            valid_items.append(
                {
                    "time": self.minutes_to_time(filler_cursor),
                    "type": "activity",
                    "title": self.context_service.localized_text(language, "nearby_walk_title", city=city),
                    "notes": self.context_service.localized_text(language, "nearby_walk_notes", city=city),
                }
            )
            filler_cursor += 90
            if is_last_day and filler_cursor >= 12 * 60:
                filler_cursor = 11 * 60
            if not is_last_day and filler_cursor >= 22 * 60:
                filler_cursor = 21 * 60

        day["timeline"] = sorted(valid_items, key=lambda item: self.parse_time_to_minutes(str(item.get("time") or "")) or 0)

    def enforce_plan_variation_and_balance(
        self,
        options: List[Dict[str, Any]],
        city: str,
        activities: List[str],
        language: str,
    ) -> List[Dict[str, Any]]:
        placeholder_pattern = re.compile(r"(kesif\s*rotasi|day\s*\d+\s*activity|activity\s*\d+)", re.IGNORECASE)
        is_tr = self.context_service.is_turkish(language)
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

                self.normalize_day_timeline(
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
