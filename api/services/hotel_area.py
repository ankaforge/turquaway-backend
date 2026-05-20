from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

import httpx


@dataclass
class HotelAreaContext:
    city: str
    zone: str
    district: str
    lat: float | None
    lng: float | None
    confidence: str


class HotelAreaResolver:
    def __init__(self, timeout_seconds: float = 8.0):
        self.timeout_seconds = timeout_seconds

    def _is_valid_coord(self, lat: float | None, lng: float | None) -> bool:
        if lat is None or lng is None:
            return False
        return abs(lat) <= 90 and abs(lng) <= 180 and not (lat == 0 and lng == 0)

    def _zone_from_address(self, city: str, address: Dict[str, Any], fallback: str) -> str:
        city_lower = (city or "").strip().lower()
        combined = " ".join(
            [
                str(address.get("city") or ""),
                str(address.get("town") or ""),
                str(address.get("county") or ""),
                str(address.get("state_district") or ""),
                str(address.get("suburb") or ""),
            ]
        ).lower()

        if city_lower == "antalya":
            if "alanya" in combined:
                return "Alanya"
            if "muratpasa" in combined or "muratpaşa" in combined or "lara" in combined or "kaleici" in combined or "kaleiçi" in combined:
                return "Muratpasa-Lara-Kaleici"
            if "konyaalti" in combined or "konyaaltı" in combined:
                return "Konyaalti"
            if "kemer" in combined:
                return "Kemer"
            if "manavgat" in combined or "side" in combined:
                return "Manavgat-Side"
            if "belek" in combined or "serik" in combined:
                return "Belek-Serik"
            if "kas" in combined or "kaş" in combined or "kalkan" in combined:
                return "Kas-Kalkan"

        if fallback:
            return fallback
        return city.title()

    def _district_from_address(self, address: Dict[str, Any]) -> str:
        return (
            str(address.get("county") or "")
            or str(address.get("state_district") or "")
            or str(address.get("town") or "")
            or str(address.get("city_district") or "")
            or str(address.get("suburb") or "")
        ).strip()

    def _fallback_zone_from_hotel_name(self, city: str, hotel_name: str) -> str:
        c = (city or "").strip().lower()
        h = (hotel_name or "").strip().lower()
        if c == "antalya":
            if any(token in h for token in ["alanya", "mahmutlar", "oba", "konakli", "konaklı", "incekum", "okurcalar", "avsallar"]):
                return "Alanya"
            if any(token in h for token in ["muratpasa", "muratpaşa", "lara", "kaleici", "kaleiçi"]):
                return "Muratpasa-Lara-Kaleici"
            if any(token in h for token in ["konyaalti", "konyaaltı"]):
                return "Konyaalti"
            if "kemer" in h:
                return "Kemer"
            if any(token in h for token in ["manavgat", "side"]):
                return "Manavgat-Side"
            if any(token in h for token in ["belek", "serik"]):
                return "Belek-Serik"
            if any(token in h for token in ["kas", "kaş", "kalkan"]):
                return "Kas-Kalkan"
        return city.title()

    def resolve(
        self,
        city: str,
        hotel_name: str,
        hotel_lat: float | None = None,
        hotel_lng: float | None = None,
    ) -> HotelAreaContext:
        city_clean = (city or "").strip() or "Unknown"
        fallback_zone = self._fallback_zone_from_hotel_name(city_clean, hotel_name)

        if not hotel_name:
            return HotelAreaContext(
                city=city_clean,
                zone=fallback_zone,
                district="",
                lat=hotel_lat,
                lng=hotel_lng,
                confidence="low",
            )

        try:
            headers = {"User-Agent": "TurquawayPlanner/1.0"}
            with httpx.Client(timeout=self.timeout_seconds, headers=headers) as client:
                if self._is_valid_coord(hotel_lat, hotel_lng):
                    reverse_resp = client.get(
                        "https://nominatim.openstreetmap.org/reverse",
                        params={
                            "lat": hotel_lat,
                            "lon": hotel_lng,
                            "format": "jsonv2",
                            "addressdetails": 1,
                        },
                    )
                    reverse_resp.raise_for_status()
                    reverse_data = reverse_resp.json() or {}
                    address = reverse_data.get("address") or {}
                    zone = self._zone_from_address(city_clean, address, fallback_zone)
                    district = self._district_from_address(address)
                    return HotelAreaContext(
                        city=city_clean,
                        zone=zone,
                        district=district,
                        lat=hotel_lat,
                        lng=hotel_lng,
                        confidence="high",
                    )

                search_resp = client.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={
                        "q": f"{hotel_name}, {city_clean}, Turkey",
                        "format": "jsonv2",
                        "limit": 1,
                        "addressdetails": 1,
                    },
                )
                search_resp.raise_for_status()
                items = search_resp.json() or []
                if items:
                    item = items[0]
                    address = item.get("address") or {}
                    lat = float(item["lat"]) if item.get("lat") else None
                    lng = float(item["lon"]) if item.get("lon") else None
                    zone = self._zone_from_address(city_clean, address, fallback_zone)
                    district = self._district_from_address(address)
                    return HotelAreaContext(
                        city=city_clean,
                        zone=zone,
                        district=district,
                        lat=lat,
                        lng=lng,
                        confidence="medium",
                    )
        except Exception:
            pass

        return HotelAreaContext(
            city=city_clean,
            zone=fallback_zone,
            district="",
            lat=hotel_lat,
            lng=hotel_lng,
            confidence="low",
        )
