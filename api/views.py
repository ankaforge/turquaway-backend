from datetime import date as date_type, timedelta
from typing import Any
from uuid import uuid4

from django.contrib.auth import authenticate
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from api.models import (
    ActivityCategory,
    Destination,
    FunnelDraft,
    Hotel,
    HotelReservation,
    Tour,
    TourReservation,
    TourSession,
    TravelPlan,
    ReservationReview,
    UserLegalConsent,
)
from api.serializers import (
    ActivityListItemSerializer,
    ChangePasswordSerializer,
    FunnelDraftSerializer,
    HotelListItemSerializer,
    HotelReservationCreateSerializer,
    HotelReservationWebhookSerializer,
    HotelSearchSerializer,
    LoginSerializer,
    MeProfileUpdateSerializer,
    MeLanguageSerializer,
    PlanConfirmSerializer,
    PlanGenerateOptionsSerializer,
    TravelPlanListItemSerializer,
    ReservationReviewCreateSerializer,
    ReservationReviewSerializer,
    RefreshTokenInputSerializer,
    RegisterSerializer,
    SuggestCitiesSerializer,
    TourListItemSerializer,
    TourReservationCreateSerializer,
    TourSearchSerializer,
)
from api.utils import GeminiService, error_response


SUPPORTED_LANGS = {"tr", "en", "ru", "ar"}


def normalize_lang(value: str | None) -> str:
    if value in SUPPORTED_LANGS:
        return value
    return "en"


def user_payload(user):
    return {
        "id": str(user.uuid),
        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone,
        "country": user.country,
        "language": user.language,
    }


def build_plan_options(
    start_date,
    end_date,
    city: str,
    currency: str = "TRY",
    activities=None,
    selected_tours=None,
    language: str = "en",
    hotel_name: str = "",
):
    total_days = max((end_date - start_date).days + 1, 1)
    options = []

    language = normalize_lang(language)
    is_tr = language == 'tr'
    is_ru = language == 'ru'
    is_ar = language == 'ar'

    def sort_timeline_items(items):
        def time_key(item):
            value = str((item or {}).get('time') or '').strip()
            parts = value.split(':')
            if len(parts) != 2:
                return 24 * 60
            try:
                return int(parts[0]) * 60 + int(parts[1])
            except ValueError:
                return 24 * 60

        return sorted(items, key=time_key)

    def text(key: str) -> str:
        translations = {
            'plan_a': {
                'tr': 'Plan A',
                'en': 'Plan A',
                'ru': 'Plan A',
                'ar': 'Al Khitta A',
            },
            'plan_b': {
                'tr': 'Plan B',
                'en': 'Plan B',
                'ru': 'Plan B',
                'ar': 'Al Khitta B',
            },
            'checkin_title': {
                'tr': 'Otele Giris ve Yerlesme',
                'en': 'Hotel Check-in and Settling In',
                'ru': 'Zaselenie v Otel i Razmeshchenie',
                'ar': 'Tasjeel Al Dukhool wa Al Istiqrar fi Al Funduq',
            },
            'checkin_notes': {
                'tr': 'Varis sonrasi dinlenme ve kisa cevre kesfi.',
                'en': 'Time to settle in after arrival and take a short walk nearby.',
                'ru': 'Vremya ustroitsya posle pribytiya i sdelat korotkuyu progulku ryadom.',
                'ar': 'Waqt lil istiqrar baad al wusool wa li jawla qasira qariba.',
            },
            'tour_notes': {
                'tr': 'Planlanan tur etkinligi.',
                'en': 'Pre-booked tour activity.',
                'ru': 'Zaranee zabronirovannaya ekskursiya.',
                'ar': 'Nashat jawla mahjooza musbaqan.',
            },
            'calm_notes': {
                'tr': 'Aileye uygun ve dengeli durak.',
                'en': 'Balanced stop suitable for a relaxed pace.',
                'ru': 'Sbalansirovannaya ostanovka dlya spokoynogo tempa.',
                'ar': 'Tawaquf mutawazin limasaar hadi.',
            },
            'dynamic_notes': {
                'tr': 'Daha dinamik rota ve kesif odagi.',
                'en': 'A more dynamic route with stronger exploration focus.',
                'ru': 'Bolee dinamichnyy marshrut s aktsentom na issledovanie.',
                'ar': 'Masaar akthar haraka ma tarkiz ala al istikshaf.',
            },
            'free_time_title': {
                'tr': f'{city} Serbest Zaman ve Dinlenme',
                'en': f'{city} Free Time and Rest',
                'ru': f'{city} Svobodnoe Vremya i Otdykh',
                'ar': f'{city} Waqt Hurr wa Raaha',
            },
            'free_time_notes': {
                'tr': 'Ulasim ve hazirlik temposuna uygun hafif program.',
                'en': 'A lighter schedule that fits arrival, preparation, and transfer pace.',
                'ru': 'Bolee legkaya programma s uchetom priezda i tempa peremeshcheniy.',
                'ar': 'Barnamaj akhaf yunasib al wusool wa tahdheer wa waqt al tanqul.',
            },
            'food_title': {
                'tr': f'{city} Yerel Lezzet Duragi',
                'en': f'{city} Local Food Stop',
                'ru': f'{city} Ostanovka dlya Mestnoy Kukhni',
                'ar': f'{city} Mahattat Atima Mahalliya',
            },
            'food_notes': {
                'tr': 'Bolgenin populer tatlarini deneme molasi.',
                'en': 'A stop to try popular flavors of the area.',
                'ru': 'Pauza, chtoby poprobovat populyarnye mestnye vkusy.',
                'ar': 'Waqfa litajrib nakehat al mantiqa al mashhoora.',
            },
            'food_notes_hotel': {
                'tr': f'{hotel_name} civarinda bolgenin populer tatlarini deneyebilecegin bir mola.' if hotel_name else 'Bolgenin populer tatlarini deneme molasi.',
                'en': f'A stop near {hotel_name} to try popular flavors of the area.' if hotel_name else 'A stop to try popular flavors of the area.',
                'ru': f'Ostanovka ryadom s {hotel_name}, chtoby poprobovat populyarnye vkusy rayona.' if hotel_name else 'Pauza, chtoby poprobovat populyarnye mestnye vkusy.',
                'ar': f'Waqfa qarib min {hotel_name} litajrib mashhoor atimat al mantiqa.' if hotel_name else 'Waqfa litajrib nakehat al mantiqa al mashhoora.',
            },
            'checkout_title': {
                'tr': 'Otelden Cikis',
                'en': 'Hotel Check-out',
                'ru': 'Vyezd iz Otelya',
                'ar': 'Tasjeel Al Khurooj Min Al Funduq',
            },
            'checkout_notes': {
                'tr': 'Donus oncesi cikis islemleri.',
                'en': 'Check-out procedures before departure.',
                'ru': 'Formalnosti vyezda pered otpravleniem.',
                'ar': 'Ijraat al khurooj qabl al mughadara.',
            },
            'summary_relaxed': {
                'tr': 'Rahat tempo',
                'en': 'Relaxed pace',
                'ru': 'Spokoynyy temp',
                'ar': 'Iqa mutarakhkh',
            },
            'summary_intense': {
                'tr': 'Yogun tempo',
                'en': 'High tempo',
                'ru': 'Intensivnyy temp',
                'ar': 'Iqa sari',
            },
        }
        return translations.get(key, {}).get(language, translations.get(key, {}).get('en', ''))

    def detailed_note(reason: str, quick_info: str, transport_minutes: int, source: str = "External", rating: str = "") -> str:
        if is_tr:
            base = (
                f"Neden: {reason}. "
                f"Kisa Bilgi: {quick_info}. "
                f"Ulasim: Otelden araba/taksi ile yaklasik {transport_minutes} dk. "
                f"Source: {source}."
            )
            if rating:
                return f"Rating: {rating}. {base}"
            return base

        base = (
            f"Why: {reason}. "
            f"Quick Info: {quick_info}. "
            f"Transport: around {transport_minutes} min by car/taxi from hotel area. "
            f"Source: {source}."
        )
        if rating:
            return f"Rating: {rating}. {base}"
        return base

    city_label = str(city or "").strip() or "City"
    hotel_label = str(hotel_name or "").strip()

    if is_tr:
        food_dishes = ["Yerel meze tabagi", "Taze deniz mahsulleri", "Bolgesel izgara", "Gunun tatlisi"]
        food_venues = [
            "Otele yakin yerel aksam yemegi",
            "Sahil kenarinda deniz mahsulleri molasi",
            "Merkezde sakin yerel yemek duragi",
            "Yerel izgara ve meze molasi",
        ]
        cafe_venues = [
            "Otele yakin kahve molasi",
            "Sahil cevresinde kahve molasi",
            "Manzarali kisa kahve molasi",
            "Merkezde sakin kahve molasi",
        ]
        activity_templates = [
            "Sahil yuruyusu ve fotograf molasi",
            "Marina cevresinde kisa kesif",
            "Sabah acik hava aktivitesi",
            "Kiyiya yakin dinlendirici rota",
            "Tarihi bolgeye yonelik kisa rota",
            "Merkezde gun batimi yuruyusu",
        ]
    elif is_ru:
        food_dishes = ["mestnye meze", "rybnoye assorti", "regionalnyy grill", "desert dnya"]
        food_venues = [
            "Uzhin s mestnoy kukhney ryadom s otelem",
            "Pauza na moreprodukty u poberezhya",
            "Spokoynyy mestnyy obed v tsentre",
            "Pauza na grill i meze",
        ]
        cafe_venues = [
            "Kofe-pauza ryadom s otelem",
            "Kofe-pauza u poberezhya",
            "Korotkaya pauza v kafe s vidom",
            "Spokoynaya kofe-pauza v tsentre",
        ]
        activity_templates = [
            "Beregovaya progulka i foto-stop",
            "Korotkoye issledovanie mariny",
            "Utrennyaya aktivnost na svezhem vozdukhe",
            "Spokoynyy marshrut ryadom s beregom",
            "Korotkiy istoricheskiy marshrut",
            "Vechernyaya progulka v tsentre",
        ]
    elif is_ar:
        food_dishes = ["mezze mahalli", "makulat bahriya", "mashwiyat mahalliya", "hulwa al yawm"]
        food_venues = [
            "wajbat mahalliya qarib min al funduq",
            "istiraha lilmakulat albahriya ala al sahil",
            "ghadaa mahalli hadi fi al markaz",
            "istiraha mashwiyat wa mezze",
        ]
        cafe_venues = [
            "istirahat qahwa qarib min al funduq",
            "istirahat qahwa ala al sahil",
            "istirahat qasira fi maqha ma itlala",
            "istirahat qahwa hadia fi al markaz",
        ]
        activity_templates = [
            "jawla ala al sahil ma mawqif suwar",
            "istikshaf qasir lihawli al marina",
            "nashat sabahi fi al talaq",
            "masar hadi qarib min al sahil",
            "masar tarikhi qasir",
            "mashy masa i fi markaz al madina",
        ]
    else:
        food_dishes = ["local meze platter", "local seafood platter", "regional grill", "dessert of the day"]
        food_venues = [
            "Local dinner stop near the hotel",
            "Seafood break by the coast",
            "Relaxed local lunch in the center",
            "Regional grill and meze stop",
        ]
        cafe_venues = [
            "Coffee break near the hotel",
            "Coffee stop by the coast",
            "Scenic cafe short break",
            "Quiet coffee break in the center",
        ]
        activity_templates = [
            "Coast walk and photo stop",
            "Short marina discovery walk",
            "Morning outdoor session",
            "Relaxed route near the coastline",
            "Historic district short route",
            "Sunset walk in the central area",
        ]

    activities = activities or []
    selected_tours = selected_tours or []
    activity_records = {
        str(item.key).strip().lower(): item
        for item in ActivityCategory.objects.filter(active=True)
    }

    def localized_activity_name(item):
        if language == 'tr':
            return item.name_tr
        if language == 'ru':
            return item.name_ru
        if language == 'ar':
            return item.name_ar
        return item.name_en

    fallback_pool = []
    for key in activities:
        key_norm = str(key).strip().lower()
        if not key_norm:
            continue
        activity_item = activity_records.get(key_norm)
        if activity_item:
            fallback_pool.append(localized_activity_name(activity_item))
            continue
        fallback_pool.append(key_norm.replace('_', ' ').title())
    if not fallback_pool:
        if is_tr:
            fallback_pool = ['Sehir Turu', 'Yerel Lezzet Deneyimi', 'Sahil Etkinligi']
        elif is_ru:
            fallback_pool = ['Progulka po Gorodu', 'Mestnaya Kulinariya', 'Otdykh u Berega']
        elif is_ar:
            fallback_pool = ['Jawla fi Al Madina', 'Tajribat Atima Mahalliya', 'Nashat Ala Al Sahil']
        else:
            fallback_pool = ['City Walk', 'Local Food Experience', 'Waterfront Activity']

    tours_by_date = {}
    unscheduled_tours = []
    for tour in selected_tours:
        session_date = tour.get('session_date')
        if session_date:
            tours_by_date.setdefault(session_date, []).append(tour)
        else:
            unscheduled_tours.append(tour)

    focus_titles = fallback_pool or activity_templates

    for idx in [1, 2]:
        days = []
        for day_index in range(total_days):
            day_no = day_index + 1
            current_date = start_date + timedelta(days=day_index)
            current_date_iso = current_date.isoformat()
            base_time = "09:00" if idx == 1 else "10:00"
            is_first_day = day_no == 1
            is_last_day = day_no == total_days
            middle_day = day_no not in (1, total_days)

            timeline_items = []

            if is_first_day:
                timeline_items.append(
                    {
                        "time": "14:00",
                        "type": "check_in",
                            "title": text('checkin_title'),
                            "notes": text('checkin_notes'),
                    }
                )

            # Use booked tours on their scheduled date.
            day_tours = list(tours_by_date.get(current_date_iso, []))

            # Distribute unscheduled tours to middle days first.
            if unscheduled_tours and (middle_day or total_days <= 2):
                day_tours.append(unscheduled_tours.pop(0))

            # For trips >=3 days, keep first/last day light.
            allow_heavy_activities = not (total_days >= 3 and (is_first_day or is_last_day))
            activity_title = focus_titles[(day_index + idx - 1) % len(focus_titles)]
            coffee_venue = cafe_venues[(day_index + idx - 1) % len(cafe_venues)]
            meal_venue = food_venues[(day_index + idx - 1) % len(food_venues)]
            local_dish = food_dishes[(day_index + idx - 1) % len(food_dishes)]

            if allow_heavy_activities:
                for tour in day_tours:
                    tour_title = tour.get('title') or f"{city} Tour"
                    timeline_items.append(
                        {
                            "time": tour.get('start_time') or base_time,
                            "type": "activity",
                            "title": tour_title,
                            "notes": detailed_note(
                                reason="Onceden rezerve edilen aktivite gunluk akisa dogrudan uyuyor" if is_tr else "Pre-booked activity fits the daily route directly",
                                quick_info=text('tour_notes'),
                                transport_minutes=20 if not is_first_day else 25,
                                source="Partner",
                            ),
                        }
                    )

                activity_reason = (
                    "Secilen aktivitelere ve butceye uygun bir durak"
                    if is_tr
                    else "A stop aligned with selected activities and budget"
                )
                activity_info = (
                    "Bolge karakterini gosteren kisa ama verimli bir rota"
                    if is_tr
                    else "A short but meaningful route reflecting the area"
                )
                timeline_items.append(
                    {
                        "time": "16:30" if day_tours else base_time,
                        "type": "activity",
                        "title": activity_title,
                        "notes": detailed_note(
                            reason=activity_reason,
                            quick_info=f"{(text('calm_notes') if idx == 1 else text('dynamic_notes'))}",
                            transport_minutes=18 if middle_day else 12,
                            source="External",
                        ) + " " + (activity_info + "."),
                    }
                )
            else:
                free_title = text('free_time_title')
                timeline_items.append(
                    {
                        "time": "17:00" if is_first_day else "09:30",
                        "type": "free_time",
                        "title": free_title,
                        "notes": detailed_note(
                            reason="Yol yorgunlugunu azaltarak gezi verimini arttirir" if is_tr else "Improves trip quality by reducing travel fatigue",
                            quick_info=text('free_time_notes'),
                            transport_minutes=8,
                            source="External",
                        ),
                    }
                )

            timeline_items.append(
                {
                    "time": "18:30" if not is_last_day else "10:30",
                    "type": "break",
                    "title": coffee_venue,
                    "notes": detailed_note(
                        reason="Yuruyus/aktivite arasi enerji dengelemesi saglar" if is_tr else "Helps balance energy between activities",
                        quick_info=(
                            f"{hotel_label} cevresine yakin kisa mola"
                            if (is_tr and hotel_label)
                            else "Near-hotel short stop"
                        ),
                        transport_minutes=10,
                        source="External",
                        rating="4.5",
                    ),
                }
            )

            # Add a dining slot for richer, user-facing plans.
            timeline_items.append(
                {
                    "time": "20:00" if is_first_day else ("11:00" if is_last_day else "13:00"),
                    "type": "dining",
                    "title": meal_venue,
                    "notes": detailed_note(
                        reason=(
                            f"Uygun fiyat ve yerel tat dengesi sundugu icin {meal_venue} oneriliyor"
                            if is_tr
                            else f"Recommended for value and local taste balance: {meal_venue}"
                        ),
                        quick_info=(
                            f"{text('food_notes_hotel')} Oneri: {local_dish}"
                            if is_tr
                            else f"{text('food_notes_hotel')} Suggested dish: {local_dish}"
                        ),
                        transport_minutes=15,
                        source="External",
                        rating="4.6",
                    ),
                }
            )

            if is_last_day:
                checkout_title = text('checkout_title')
                timeline_items.append(
                    {
                        "time": "12:00",
                        "type": "check_out",
                        "title": checkout_title,
                        "notes": text('checkout_notes'),
                    }
                )

            days.append(
                {
                    "day": day_no,
                    "timeline": sort_timeline_items(timeline_items),
                }
            )

        options.append(
            {
                "plan_id": f"plan_{idx}_{uuid4().hex[:10]}",
                "title": (
                    ("Yuksek Tempolu Kesif" if is_tr else "High Tempo Discovery")
                    if idx == 1
                    else ("Sakin ve Dengeli Rota" if is_tr else "Calm and Relaxed Route")
                ),
                "gemini_recommendation": (
                    (
                        f"{city} icin {total_days} gunluk, otele yakin duraklar ve yerel lezzetler iceren dengeli plan."
                        if is_tr else
                        f"A {total_days}-day balanced plan for {city} with nearby stops and local food suggestions."
                        if not (is_ru or is_ar) else
                        f"{city} {total_days}-dnevny plan s blizkimi ostanovkami i mestnoy edoy."
                        if is_ru else
                        f"Khutta limuddat {total_days} ayam fi {city} tatadamman amaakin qariba wa atima mahalliya."
                    ) if idx == 1 else (
                        f"{city} icin {total_days} gunluk, daha hareketli ve fotograf duraklari guclu kesif plani."
                        if is_tr else
                        f"A {total_days}-day more dynamic discovery plan for {city} with stronger photo stops."
                        if not (is_ru or is_ar) else
                        f"{city} {total_days}-dnevnyy bolee dinamichnyy plan s yarkimi foto-tochkami."
                        if is_ru else
                        f"Khutta akthar haraka limuddat {total_days} ayam fi {city} ma tawqofat suwar mumayyaza."
                    )
                ),
                "summary": (
                    f"{total_days} Gun • {text('summary_intense') if idx == 1 else text('summary_relaxed')}"
                    if is_tr else
                    f"{total_days} Days • {text('summary_intense') if idx == 1 else text('summary_relaxed')}"
                ),
                "days": days,
                "estimated_total": 12400 if idx == 1 else 13800,
                "currency": currency,
            }
        )
    return options


def _is_valid_timeline_item(item: Any) -> bool:
    if not isinstance(item, dict):
        return False
    required_keys = ["time", "type", "title", "notes"]
    return all(bool(str(item.get(key, "")).strip()) for key in required_keys)


def _is_valid_day_item(item: Any) -> bool:
    if not isinstance(item, dict):
        return False
    if "day" not in item or not isinstance(item.get("timeline"), list):
        return False
    return all(_is_valid_timeline_item(timeline_item) for timeline_item in item["timeline"])


def _is_valid_plan_option(item: Any) -> bool:
    if not isinstance(item, dict):
        return False
    required_keys = ["plan_id", "title", "estimated_total", "currency", "days"]
    if not all(key in item for key in required_keys):
        return False
    if not str(item.get("plan_id", "")).strip() or not str(item.get("title", "")).strip():
        return False
    if "summary" not in item and "description" not in item:
        return False
    if not isinstance(item.get("days"), list):
        return False
    return all(_is_valid_day_item(day_item) for day_item in item["days"])


def _is_valid_options_payload(options: Any) -> bool:
    if not isinstance(options, list) or not options:
        return False
    return all(_is_valid_plan_option(option) for option in options)


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="validation_error",
                detail="Register validation failed.",
                fields=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.save()
        consents = serializer.validated_data["consents"]
        accepted_at = parse_datetime(consents["accepted_at"])
        if accepted_at is None:
            return error_response(
                code="validation_error",
                detail="accepted_at must be a valid ISO datetime.",
                fields={"consents": {"accepted_at": ["Invalid datetime."]}},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        UserLegalConsent.objects.create(
            user=user,
            terms_accepted=consents["terms_accepted"],
            privacy_accepted=consents["privacy_accepted"],
            accepted_at=accepted_at,
            version=consents["version"],
        )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": user_payload(user),
                "tokens": {
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="validation_error",
                detail="Login validation failed.",
                fields=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(
            request,
            username=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            return error_response(
                code="invalid_credentials",
                detail="Email or password is incorrect.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": {
                    "id": str(user.uuid),
                    "full_name": user.full_name,
                    "email": user.email,
                    "language": user.language,
                },
                "tokens": {
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh),
                },
            }
        )


class RefreshTokenView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RefreshTokenInputSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="validation_error",
                detail="Refresh token validation failed.",
                fields=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(serializer.validated_data["refresh_token"])
            return Response({"access_token": str(token.access_token)})
        except Exception:
            return error_response(
                code="invalid_token",
                detail="Refresh token is invalid.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = RefreshTokenInputSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="validation_error",
                detail="Refresh token validation failed.",
                fields=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(serializer.validated_data["refresh_token"])
            token.blacklist()
        except Exception:
            return error_response(
                code="invalid_token",
                detail="Refresh token is invalid.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(user_payload(request.user))

    def patch(self, request):
        serializer = MeProfileUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code='validation_error',
                detail='Profile update validation failed.',
                fields=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        request.user.full_name = serializer.validated_data['full_name']
        request.user.phone = serializer.validated_data['phone']
        request.user.country = serializer.validated_data['country']
        request.user.save(update_fields=['full_name', 'phone', 'country'])

        return Response(user_payload(request.user))


class MePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return error_response(
                code='validation_error',
                detail='Password change validation failed.',
                fields=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save(update_fields=['password'])
        return Response({'detail': 'Password updated successfully.'})


class MeLanguageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        serializer = MeLanguageSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="validation_error",
                detail="Language validation failed.",
                fields=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        request.user.language = serializer.validated_data["language"]
        request.user.save(update_fields=["language"])
        return Response({"language": request.user.language})


def _hotel_status_for_frontend(reservation: HotelReservation) -> str:
    if reservation.status == HotelReservation.Status.BOOKING_CANCELLED:
        return 'cancelled'
    if reservation.end_date and reservation.end_date < timezone.localdate():
        return 'completed'
    return 'active'


def _tour_status_for_frontend(reservation: TourReservation) -> str:
    if reservation.status == TourReservation.Status.CANCELLED:
        return 'cancelled'
    tour_date = reservation.session.date if reservation.session else None
    if tour_date and tour_date < timezone.localdate():
        return 'completed'
    if reservation.status in [TourReservation.Status.CONFIRMED, TourReservation.Status.NO_SHOW]:
        return 'completed'
    return 'active'


def _travel_plan_trip_dates(plan: TravelPlan):
    raw_start = plan.source_payload.get('start_date')
    raw_end = plan.source_payload.get('end_date')

    try:
        start_date = date_type.fromisoformat(raw_start) if raw_start else None
    except (TypeError, ValueError):
        start_date = None

    try:
        end_date = date_type.fromisoformat(raw_end) if raw_end else None
    except (TypeError, ValueError):
        end_date = None

    return start_date, end_date


class MeReservationsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        reservation_type = (request.query_params.get('type') or '').strip().lower()
        if reservation_type not in ['hotel', 'tour']:
            return error_response(
                code='validation_error',
                detail='type must be hotel or tour.',
                fields={'type': ['Use hotel or tour.']},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if reservation_type == 'hotel':
            results = []
            qs = HotelReservation.objects.filter(user=request.user).select_related('hotel__destination').order_by('-start_date')
            for item in qs:
                results.append(
                    {
                        'reservation_id': str(item.uuid),
                        'name': item.hotel.name,
                        'city': item.hotel.destination.name if item.hotel.destination else '',
                        'check_in': item.start_date,
                        'check_out': item.end_date,
                        'status': _hotel_status_for_frontend(item),
                    }
                )
            return Response({'results': results})

        results = []
        qs = (
            TourReservation.objects.filter(user=request.user)
            .select_related('session__tour__destination')
            .order_by('-session__date')
        )
        for item in qs:
            tour = item.session.tour if item.session and item.session.tour else None
            results.append(
                {
                    'reservation_id': str(item.uuid),
                    'title': tour.title if tour else '',
                    'city': tour.destination.name if tour and tour.destination else '',
                    'tour_date': item.session.date if item.session else None,
                    'status': _tour_status_for_frontend(item),
                }
            )
        return Response({'results': results})


class MeReservationVoucherView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, reservation_id: str):
        hotel_res = HotelReservation.objects.filter(user=request.user, uuid=reservation_id).first()
        if hotel_res:
            return Response({'url': f'https://cdn.example.com/vouchers/{hotel_res.uuid}.pdf'})

        tour_res = TourReservation.objects.filter(user=request.user, uuid=reservation_id).first()
        if tour_res:
            return Response({'url': f'https://cdn.example.com/vouchers/{tour_res.uuid}.pdf'})

        return error_response(
            code='not_found',
            detail='Reservation not found.',
            status_code=status.HTTP_404_NOT_FOUND,
        )


class MeEligibleReviewReservationsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        results = []
        today = timezone.localdate()

        hotel_qs = HotelReservation.objects.filter(user=request.user).select_related('hotel__destination')
        for item in hotel_qs:
            if _hotel_status_for_frontend(item) != 'completed':
                continue
            review = ReservationReview.objects.filter(user=request.user, hotel_reservation=item).first()
            results.append(
                {
                    'reservation_id': str(item.uuid),
                    'name': item.hotel.name,
                    'city': item.hotel.destination.name if item.hotel.destination else '',
                    'reservation_date': item.end_date,
                    'rated': bool(review),
                    'rating': review.rating if review else None,
                    'feedback': review.feedback if review else '',
                }
            )

        tour_qs = TourReservation.objects.filter(user=request.user).select_related('session__tour__destination')
        for item in tour_qs:
            if _tour_status_for_frontend(item) != 'completed':
                continue
            review = ReservationReview.objects.filter(user=request.user, tour_reservation=item).first()
            tour = item.session.tour if item.session and item.session.tour else None
            reservation_date = item.session.date if item.session else today
            results.append(
                {
                    'reservation_id': str(item.uuid),
                    'name': tour.title if tour else '',
                    'city': tour.destination.name if tour and tour.destination else '',
                    'reservation_date': reservation_date,
                    'rated': bool(review),
                    'rating': review.rating if review else None,
                    'feedback': review.feedback if review else '',
                }
            )

        return Response({'results': results})


class MeReviewsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ReservationReviewCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code='validation_error',
                detail='Review validation failed.',
                fields=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        reservation_uuid = serializer.validated_data['reservation_id']
        rating = serializer.validated_data['rating']
        feedback = serializer.validated_data.get('feedback', '')

        hotel_res = HotelReservation.objects.filter(user=request.user, uuid=reservation_uuid).first()
        if hotel_res:
            if ReservationReview.objects.filter(user=request.user, hotel_reservation=hotel_res).exists():
                return error_response(
                    code='conflict',
                    detail='Review already exists for this reservation.',
                    status_code=status.HTTP_409_CONFLICT,
                )
            review = ReservationReview.objects.create(
                user=request.user,
                hotel_reservation=hotel_res,
                rating=rating,
                feedback=feedback,
            )
            return Response(ReservationReviewSerializer(review).data, status=status.HTTP_201_CREATED)

        tour_res = TourReservation.objects.filter(user=request.user, uuid=reservation_uuid).first()
        if tour_res:
            if ReservationReview.objects.filter(user=request.user, tour_reservation=tour_res).exists():
                return error_response(
                    code='conflict',
                    detail='Review already exists for this reservation.',
                    status_code=status.HTTP_409_CONFLICT,
                )
            review = ReservationReview.objects.create(
                user=request.user,
                tour_reservation=tour_res,
                rating=rating,
                feedback=feedback,
            )
            return Response(ReservationReviewSerializer(review).data, status=status.HTTP_201_CREATED)

        return error_response(
            code='not_found',
            detail='Reservation not found.',
            status_code=status.HTTP_404_NOT_FOUND,
        )


class FunnelDraftView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        serializer = FunnelDraftSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="validation_error",
                detail="Draft validation failed.",
                fields=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        defaults = serializer.validated_data
        draft, _ = FunnelDraft.objects.update_or_create(user=request.user, defaults=defaults)
        return Response({"draft_id": str(draft.uuid), "updated_at": draft.updated_at.isoformat()})

    def get(self, request):
        draft = FunnelDraft.objects.filter(user=request.user).first()
        if not draft:
            return Response(
                {
                    "start_date": None,
                    "end_date": None,
                    "adults": 1,
                    "children": 0,
                    "budget_type": "economy",
                    "activities": [],
                    "language": normalize_lang(request.user.language),
                }
            )

        return Response(
            {
                "start_date": draft.start_date,
                "end_date": draft.end_date,
                "adults": draft.adults,
                "children": draft.children,
                "budget_type": draft.budget_type,
                "activities": draft.activities,
                "language": normalize_lang(draft.language),
            }
        )


class ActivityListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        lang = normalize_lang(request.query_params.get("lang") or request.query_params.get("language"))
        activities = ActivityCategory.objects.filter(active=True).order_by("id")
        data = ActivityListItemSerializer(activities, many=True, context={"lang": lang}).data
        return Response({"results": data})


class SuggestCitiesView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SuggestCitiesSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="validation_error",
                detail="Suggest cities validation failed.",
                fields=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        payload = serializer.validated_data
        destination_qs = Destination.objects.filter(active=True, tours__is_approved=True)

        activities = payload.get("activities") or []
        if activities:
            destination_qs = destination_qs.filter(tours__categories__key__in=activities)

        if payload.get("children", 0) > 0:
            destination_qs = destination_qs.filter(tours__family_friendly=True)

        allowed_destinations = list(destination_qs.order_by("name").distinct().values_list("name", flat=True))
        if not allowed_destinations:
            return Response({"cities": []}, status=status.HTTP_200_OK)

        try:
            suggestions = GeminiService().get_city_suggestions(
                budget=payload["budget_type"],
                activities=activities,
                language=normalize_lang(payload.get("language")),
                allowed_destinations=allowed_destinations,
            )
        except Exception:
            fallback = []
            for name in allowed_destinations[:3]:
                fallback.append({"city": name, "description": "Butce ve aktivite tercihine uygun onerilen rota"})
            return Response({"cities": fallback})

        cities = suggestions[:3]
        while len(cities) < 3:
            cities.append(
                {
                    "city": allowed_destinations[len(cities) % len(allowed_destinations)],
                    "description": "Onerilen alternatif rota",
                }
            )

        return Response({"cities": cities[:3]})


class HotelSearchView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = HotelSearchSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="validation_error",
                detail="Hotel search validation failed.",
                fields=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        payload = serializer.validated_data
        qs = Hotel.objects.filter(destination__name__iexact=payload["city"])

        budget = payload["budget_type"]
        if budget == "cheap":
            qs = qs.filter(nightly_price_per_person__lt=5000)
        elif budget == "economy":
            qs = qs.filter(nightly_price_per_person__lt=8000)
        elif budget == "luxury":
            qs = qs.filter(nightly_price_per_person__gt=12000)

        sort = payload["sort"]
        if sort == "price_asc":
            qs = qs.order_by("nightly_price_per_person")
        elif sort == "price_desc":
            qs = qs.order_by("-nightly_price_per_person")
        else:
            qs = qs.order_by(F("rating").desc(), F("nightly_price_per_person").asc())

        hotels_data = HotelListItemSerializer(qs, many=True).data
        try:
            ranked_ids = GeminiService().rank_hotels(
                hotels=hotels_data,
                budget=payload["budget_type"],
                activities=payload.get("activities", []),
                language=normalize_lang(payload.get("language")),
            )
            if ranked_ids:
                order_map = {hotel_id: idx for idx, hotel_id in enumerate(ranked_ids)}
                hotels_data = sorted(
                    hotels_data,
                    key=lambda item: order_map.get(str(item.get("id")), len(order_map) + 1),
                )
        except Exception:
            pass

        return Response({"hotels": hotels_data})


class HotelReservationCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = HotelReservationCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="validation_error",
                detail="Hotel reservation validation failed.",
                fields=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        payload = serializer.validated_data
        hotel = Hotel.objects.filter(uuid=payload["hotel_id"]).first()
        if not hotel:
            return error_response(
                code="not_found",
                detail="Hotel not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        payment_intent = f"pi_{uuid4().hex[:16]}"
        reservation = HotelReservation.objects.create(
            user=request.user,
            hotel=hotel,
            start_date=payload["start_date"],
            end_date=payload["end_date"],
            adults=payload["adults"],
            children=payload["children"],
            payment_intent_id=payment_intent,
        )

        return Response(
            {
                "reservation_id": str(reservation.uuid),
                "status": reservation.status,
                "payment": {
                    "provider": "booking_demand_partner",
                    "payment_intent_id": payment_intent,
                    "client_secret": f"secret_{uuid4().hex[:16]}",
                },
            },
            status=status.HTTP_201_CREATED,
        )


class HotelReservationWebhookView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = HotelReservationWebhookSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="validation_error",
                detail="Webhook payload validation failed.",
                fields=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        payload = serializer.validated_data
        reservation = HotelReservation.objects.filter(
            payment_intent_id=payload["payment_intent_id"]
        ).first()
        if not reservation:
            return error_response(
                code="not_found",
                detail="Reservation not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        event_to_status = {
            "payment_succeeded": HotelReservation.Status.PAYMENT_SUCCEEDED,
            "payment_failed": HotelReservation.Status.BOOKING_CANCELLED,
            "booking_confirmed": HotelReservation.Status.BOOKING_CONFIRMED,
            "booking_cancelled": HotelReservation.Status.BOOKING_CANCELLED,
        }
        reservation.status = event_to_status[payload["event"]]
        reservation.save(update_fields=["status"])
        return Response({"status": "ok"})


class TourSearchView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = TourSearchSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="validation_error",
                detail="Tour search validation failed.",
                fields=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        payload = serializer.validated_data
        qs = Tour.objects.filter(destination__name__iexact=payload["city"], is_approved=True)

        if payload["children"] > 0:
            qs = qs.filter(family_friendly=True)

        activity_keys = payload.get("activities") or []
        if activity_keys:
            qs = qs.filter(categories__key__in=activity_keys).distinct()

        tours = TourListItemSerializer(qs.order_by("title", "id"), many=True).data
        try:
            ranked_ids = GeminiService().rank_tours(
                tours=tours,
                budget=payload["budget_type"],
                activities=activity_keys,
                language=normalize_lang(payload.get("language")),
                family_mode=payload["children"] > 0,
            )
            if ranked_ids:
                order_map = {tour_id: idx for idx, tour_id in enumerate(ranked_ids)}
                tours = sorted(
                    tours,
                    key=lambda item: order_map.get(str(item.get("id")), len(order_map) + 1),
                )
        except Exception:
            pass

        if not tours:
            return Response(
                {
                    "tours": [],
                    "empty_state": True,
                    "diy_fallback": {
                        "title": "Kendin Yap Rota",
                        "summary": "Bolgede anlasmali tur yok, sana ozel serbest gezi plani olusturuldu.",
                    },
                }
            )

        return Response({"tours": tours, "empty_state": False, "diy_fallback": None})


class TourReservationCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = TourReservationCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="validation_error",
                detail="Tour reservation validation failed.",
                fields=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        vd = serializer.validated_data

        hotel_reservation = None
        if vd.get('hotel_reservation_id'):
            hotel_reservation = HotelReservation.objects.filter(
                uuid=vd['hotel_reservation_id'], user=request.user
            ).first()
            if hotel_reservation is None:
                return error_response(
                    code="not_found",
                    detail="Hotel reservation not found or does not belong to you.",
                    status_code=status.HTTP_404_NOT_FOUND,
                )

        adults = vd['adults']
        children = vd.get('children', 0)

        try:
            with transaction.atomic():
                session = TourSession.objects.select_for_update().select_related('tour').get(pk=vd['session_id'])

                if TourReservation.objects.filter(user=request.user, session=session).exists():
                    return error_response(
                        code='conflict',
                        detail='You already have a reservation for this session.',
                        status_code=status.HTTP_409_CONFLICT,
                    )

                available = session.capacity - session.booked_count
                if adults + children > available:
                    return error_response(
                        code='validation_error',
                        detail='Tour reservation validation failed.',
                        fields={'session_id': [f'Not enough spots. Available: {available}.']},
                        status_code=status.HTTP_400_BAD_REQUEST,
                    )

                total_price = (
                    session.tour.price_adult * adults
                    + session.tour.price_child * children
                )

                reservation = TourReservation.objects.create(
                    user=request.user,
                    session=session,
                    hotel_reservation=hotel_reservation,
                    adults=adults,
                    children=children,
                    total_price=total_price,
                    status=TourReservation.Status.PENDING,
                )

                TourSession.objects.filter(pk=session.pk).update(
                    booked_count=F('booked_count') + adults + children
                )
        except IntegrityError:
            return error_response(
                code='conflict',
                detail='You already have a reservation for this session.',
                status_code=status.HTTP_409_CONFLICT,
            )

        return Response(
            {
                "reservation_id": str(reservation.uuid),
                "status": reservation.status,
                "tour": {
                    "id": str(session.tour.uuid),
                    "title": session.tour.title,
                },
                "session": {
                    "session_id": session.pk,
                    "date": session.date,
                    "start_time": session.start_time,
                    "end_time": session.end_time,
                },
                "adults": adults,
                "children": children,
                "total_price": total_price,
                "currency": session.tour.currency,
            },
            status=status.HTTP_201_CREATED,
        )


class PlanGenerateOptionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PlanGenerateOptionsSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="validation_error",
                detail="Plan options validation failed.",
                fields=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        payload = serializer.validated_data
        start_d = payload["start_date"]
        end_d = payload["end_date"]
        effective_language = normalize_lang(getattr(request.user, "language", None) or payload.get("language"))

        # Resolve hotel name for Gemini context
        hotel_name = ''
        hotel_lat = None
        hotel_lng = None
        hotel_reservation_id = payload.get("hotel_reservation_id")
        if hotel_reservation_id:
            hotel_res = (
                HotelReservation.objects
                .filter(uuid=hotel_reservation_id, user=request.user)
                .select_related('hotel')
                .first()
            )
            if not hotel_res:
                return error_response(
                    code="not_found",
                    detail="hotel_reservation_id not found or does not belong to you.",
                    fields={"hotel_reservation_id": ["Invalid value."]},
                    status_code=status.HTTP_404_NOT_FOUND,
                )
            hotel_name = hotel_res.hotel.name
            hotel_lat = hotel_res.hotel.lat
            hotel_lng = hotel_res.hotel.lng

        # Candidate partner tours for requested city/activity scope.
        candidate_partner_tours = []
        partner_qs = Tour.objects.filter(destination__name__iexact=payload["city"], is_approved=True)
        activity_keys = payload.get("activities") or []
        if activity_keys:
            partner_qs = partner_qs.filter(categories__key__in=activity_keys).distinct()
        for partner_tour in partner_qs.select_related('destination').order_by('title')[:40]:
            primary_category = partner_tour.categories.values_list('key', flat=True).first() or 'general'
            provider_phone = ''
            provider_name = ''
            if partner_tour.provider:
                provider_name = partner_tour.provider.company_name
                if getattr(partner_tour.provider, 'user_id', None):
                    provider_phone = str(getattr(partner_tour.provider.user, 'phone', '') or '').strip()
            candidate_partner_tours.append(
                {
                    'title': partner_tour.title,
                    'category': primary_category,
                    'area': partner_tour.destination.name if partner_tour.destination else payload["city"],
                    'price_level': payload.get("budget_type", "economy"),
                    'provider_name': provider_name,
                    'phone': provider_phone,
                    'website': partner_tour.location_link or '',
                }
            )

        # Resolve selected tour details with sessions within travel dates for Gemini context
        selected_tours_detail = []
        selected_tour_ids = payload.get("selected_tour_ids") or []
        if selected_tour_ids:
            for tour in Tour.objects.filter(uuid__in=selected_tour_ids).prefetch_related('sessions'):
                session = (
                    tour.sessions
                    .filter(is_active=True, date__range=(start_d, end_d))
                    .order_by('date', 'start_time')
                    .first()
                )
                selected_tours_detail.append({
                    'title': tour.title,
                    'session_date': session.date.isoformat() if session else None,
                    'start_time': session.start_time.strftime('%H:%M') if session else None,
                    'end_time': session.end_time.strftime('%H:%M') if session else None,
                    'includes_food': getattr(tour, 'includes_free_food_drinks', False),
                    'includes_transfer': getattr(tour, 'includes_hotel_pickup_dropoff', False),
                })

        try:
            options = GeminiService().generate_plan_options(
                city=payload["city"],
                start_date=start_d.isoformat(),
                end_date=end_d.isoformat(),
                budget=payload["budget_type"],
                activities=payload["activities"],
                adults=payload["adults"],
                children=payload["children"],
                language=effective_language,
                family_mode=payload.get("family_mode", False),
                hotel_name=hotel_name,
                hotel_lat=hotel_lat,
                hotel_lng=hotel_lng,
                selected_tours=selected_tours_detail,
                partner_tours=candidate_partner_tours,
            )
            if not _is_valid_options_payload(options):
                raise ValueError("Invalid or empty options payload from AI provider.")
        except Exception as e:
            print(f"CRITICAL GEMINI ERROR: {e}")
            options = build_plan_options(
                start_d,
                end_d,
                payload["city"],
                activities=payload.get("activities"),
                selected_tours=selected_tours_detail,
                language=effective_language,
                hotel_name=hotel_name,
            )

        destination = Destination.objects.filter(name__iexact=payload["city"]).first()
        plan = TravelPlan.objects.create(
            user=request.user,
            destination=destination,
            source_payload={
                "city": payload["city"],
                "start_date": start_d.isoformat(),
                "end_date": end_d.isoformat(),
                "adults": payload["adults"],
                "children": payload["children"],
                "budget_type": payload["budget_type"],
                "activities": payload["activities"],
                "hotel_reservation_id": str(hotel_reservation_id) if hotel_reservation_id else None,
                "selected_tour_ids": [str(x) for x in payload.get("selected_tour_ids", [])],
                "language": effective_language,
                "family_mode": payload["family_mode"],
            },
            options_payload=options,
            status=TravelPlan.Status.DRAFT,
        )
        request.session["last_plan_uuid"] = str(plan.uuid)

        return Response({"options": options})


class PlanConfirmView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PlanConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                code="validation_error",
                detail="Plan confirm validation failed.",
                fields=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        plan_id = serializer.validated_data["plan_id"]
        travel_plan = (
            TravelPlan.objects.filter(user=request.user)
            .exclude(options_payload=[])
            .order_by("-created_at")
            .first()
        )
        if not travel_plan:
            return error_response(
                code="not_found",
                detail="No generated plan found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        option = next((item for item in travel_plan.options_payload if item.get("plan_id") == plan_id), None)
        if not option:
            return error_response(
                code="not_found",
                detail="plan_id not found in generated options.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        travel_plan.confirmed_plan_id = plan_id
        travel_plan.status = TravelPlan.Status.ACTIVE
        travel_plan.save(update_fields=["confirmed_plan_id", "status"])

        selected_tour_ids = travel_plan.source_payload.get("selected_tour_ids") or []
        created_count = 0
        if selected_tour_ids:
            hotel_reservation = None
            hotel_reservation_id = travel_plan.source_payload.get("hotel_reservation_id")
            if hotel_reservation_id:
                hotel_reservation = HotelReservation.objects.filter(uuid=hotel_reservation_id).first()

            # Prefer sessions within travel date range
            from datetime import date as date_type
            raw_start = travel_plan.source_payload.get("start_date")
            raw_end = travel_plan.source_payload.get("end_date")
            trip_start = date_type.fromisoformat(raw_start) if raw_start else None
            trip_end = date_type.fromisoformat(raw_end) if raw_end else None

            adults = travel_plan.source_payload.get("adults", 1)
            children = travel_plan.source_payload.get("children", 0)
            needed = adults + children

            tours = Tour.objects.filter(uuid__in=selected_tour_ids)
            for tour in tours:
                with transaction.atomic():
                    session_qs = TourSession.objects.select_for_update().filter(tour=tour, is_active=True)
                    if trip_start and trip_end:
                        session = (
                            session_qs
                            .filter(date__range=(trip_start, trip_end))
                            .order_by('date', 'start_time')
                            .first()
                        ) or session_qs.order_by('date', 'start_time').first()
                    else:
                        session = session_qs.order_by('date', 'start_time').first()

                    if session is None:
                        continue

                    if TourReservation.objects.filter(user=request.user, session=session).exists():
                        continue

                    available = session.capacity - session.booked_count
                    if available < needed:
                        continue

                    TourReservation.objects.create(
                        user=request.user,
                        session=session,
                        hotel_reservation=hotel_reservation,
                        adults=adults,
                        children=children,
                        total_price=(
                            tour.price_adult * adults
                            + tour.price_child * children
                        ),
                        status=TourReservation.Status.CONFIRMED,
                    )
                    TourSession.objects.filter(pk=session.pk).update(
                        booked_count=F('booked_count') + needed
                    )
                    created_count += 1

        return Response(
            {
                "status": "confirmed",
                "confirmed_plan_id": plan_id,
                "tour_reservations_created": created_count,
            }
        )


class PlanCurrentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        travel_plan = (
            TravelPlan.objects.filter(user=request.user, status=TravelPlan.Status.ACTIVE)
            .order_by("-created_at")
            .first()
        )
        if not travel_plan:
            return error_response(
                code="not_found",
                detail="No active plan found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        option = next(
            (item for item in travel_plan.options_payload if item.get("plan_id") == travel_plan.confirmed_plan_id),
            None,
        )
        if not option and travel_plan.options_payload:
            option = travel_plan.options_payload[0]

        return Response(
            {
                "plan_id": travel_plan.confirmed_plan_id,
                "city": travel_plan.source_payload.get("city", ""),
                "status": "active",
                "days": (option or {}).get("days", []),
            }
        )


class PlanListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        status_filter = (request.query_params.get('status') or 'all').strip().lower()
        if status_filter not in {'all', 'ongoing', 'upcoming', 'past'}:
            return error_response(
                code='validation_error',
                detail='status must be one of ongoing, upcoming, past, all.',
                fields={'status': ['Use ongoing, upcoming, past, or all.']},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        plans = list(
            TravelPlan.objects.filter(
                user=request.user,
                status__in=[TravelPlan.Status.ACTIVE, TravelPlan.Status.COMPLETED],
            )
            .select_related('destination')
            .order_by('-created_at')
        )

        today = timezone.localdate()
        if status_filter != 'all':
            filtered_plans = []
            for plan in plans:
                start_date, end_date = _travel_plan_trip_dates(plan)
                if not start_date or not end_date:
                    continue

                if status_filter == 'ongoing' and start_date <= today <= end_date:
                    filtered_plans.append(plan)
                elif status_filter == 'upcoming' and start_date > today:
                    filtered_plans.append(plan)
                elif status_filter == 'past' and end_date < today:
                    filtered_plans.append(plan)
            plans = filtered_plans

        serialized = TravelPlanListItemSerializer(plans, many=True)
        return Response({'count': len(serialized.data), 'results': serialized.data})


class PlanRestartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        FunnelDraft.objects.filter(user=request.user).delete()
        TravelPlan.objects.filter(user=request.user, status__in=[TravelPlan.Status.DRAFT, TravelPlan.Status.ACTIVE]).update(
            status=TravelPlan.Status.COMPLETED
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
