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

    def generate_plan_text(
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
    ) -> str:
        area_ctx = self.hotel_area_resolver.resolve(
            city=city,
            hotel_name=hotel_name,
            hotel_lat=hotel_lat,
            hotel_lng=hotel_lng,
        )

        # Sadeleştirilmiş, doğal metin odaklı prompt
        prompt = f"""
Sen bir seyahat planlama uzmanısın. Kullanıcı için Alanya'da, {hotel_name} otelinde {start_date} - {end_date} tarihleri arasında, {budget} bütçeyle, {', '.join(activities)} odaklı, iki kişilik bir tatil planı oluşturacaksın.

Kullanıcı istekleri:
- Otel rezervasyonu yapılmış.
- 4 yıldızın altında kafe ve restoran önermemelisin.
- Otelden çok uzak turlar ve mekanlar önermemelisin.
- Turlar için gezi turu düzenleyen şirketlerin adını da belirt.
- Akşam 18:00 sonrası otel çevresinden çok uzaklaştırma.
- Yöresel yeme içme, arada kahve/soğuk içecek molaları, tekne turu, Alanya civarındaki antik kentlere arkeolojik gezi, tüplü dalış isteniyor.

Planı, insan gibi, akıcı ve detaylı şekilde, gün gün başlıklarla yaz. Her gün için sabah, öğle, akşam ve mola önerilerini, mekan isimleriyle birlikte belirt. Bütçe ve zaman kısıtlarını göz önünde bulundur. Akşamları otel çevresine yakın öneriler ver. Her gün için önerdiğin mekanların kısa açıklamasını ve neden önerdiğini de ekle. Turlar ve aktiviteler için mümkünse şirket adı ve tahmini fiyat belirt. Planı tamamen doğal, akıcı metin olarak üret. JSON, tablo veya madde işareti kullanma. Sadece metin olarak yaz.

Kullanıcı dili: {language}
""".strip()

        response = self.client.chat_json(prompt=prompt, temperature=0.45)
        # Modelin döndürdüğü metni doğrudan al
        plan_text = response.get("text") or next(iter(response.values()), "")
        return plan_text
