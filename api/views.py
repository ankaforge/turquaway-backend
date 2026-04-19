from datetime import date as date_type, timedelta
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
):
    total_days = max((end_date - start_date).days + 1, 1)
    options = []

    activities = activities or []
    selected_tours = selected_tours or []
    activity_titles = {
        'swimming': 'Sahil Yuzme Etkinligi',
        'culture': 'Tarihi Bolge Yuruyus Turu',
        'food': 'Yerel Lezzet Deneyimi',
        'food_drink': 'Yerel Lezzet Deneyimi',
        'yeme_icme': 'Yerel Lezzet Deneyimi',
        'safari': 'Doga ve Safari Turu',
        'diving': 'Dalis ve Tekne Aktivitesi',
        'boat': 'Tekne Turu',
        'nature': 'Doga Kesif Rotasi',
        'kultur': 'Tarihi Bolge Yuruyus Turu',
        'yuzme': 'Sahil Yuzme Etkinligi',
    }

    fallback_pool = []
    for key in activities:
        key_norm = str(key).strip().lower()
        if not key_norm:
            continue
        if key_norm in activity_titles:
            fallback_pool.append(activity_titles[key_norm])
        else:
            fallback_pool.append(key_norm.replace('_', ' ').title())
    if not fallback_pool:
        fallback_pool = ['Sehir Turu', 'Yerel Lezzet Deneyimi', 'Sahil Etkinligi']

    tours_by_date = {}
    unscheduled_tours = []
    for tour in selected_tours:
        session_date = tour.get('session_date')
        if session_date:
            tours_by_date.setdefault(session_date, []).append(tour)
        else:
            unscheduled_tours.append(tour)

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
                        "title": "Otele Giris ve Yerlesme",
                        "notes": "Varis sonrasi dinlenme ve kisa cevre kesfi.",
                    }
                )

            # Use booked tours on their scheduled date.
            day_tours = list(tours_by_date.get(current_date_iso, []))

            # Distribute unscheduled tours to middle days first.
            if unscheduled_tours and (middle_day or total_days <= 2):
                day_tours.append(unscheduled_tours.pop(0))

            # For trips >=3 days, keep first/last day light.
            allow_heavy_activities = not (total_days >= 3 and (is_first_day or is_last_day))

            if allow_heavy_activities:
                for tour in day_tours:
                    timeline_items.append(
                        {
                            "time": tour.get('start_time') or base_time,
                            "type": "activity",
                            "title": tour.get('title') or f"{city} Ozel Turu",
                            "notes": "Planlanan tur etkinligi.",
                        }
                    )

                fallback_title = fallback_pool[(day_index + idx - 1) % len(fallback_pool)]
                timeline_items.append(
                    {
                        "time": "16:30" if day_tours else base_time,
                        "type": "activity",
                        "title": f"{city} {fallback_title}",
                        "notes": "Aileye uygun" if idx == 1 else "Daha dinamik rota",
                    }
                )
            else:
                timeline_items.append(
                    {
                        "time": "17:00" if is_first_day else "09:30",
                        "type": "free_time",
                        "title": f"{city} Serbest Zaman ve Dinlenme",
                        "notes": "Ulasim ve hazirlik temposuna uygun hafif program.",
                    }
                )

            # Add a dining slot for richer, user-facing plans.
            timeline_items.append(
                {
                    "time": "20:00" if is_first_day else "13:00",
                    "type": "dining",
                    "title": f"{city} Yerel Lezzet Duragi",
                    "notes": "Bolgenin populer tatlarini deneme molasi.",
                }
            )

            if is_last_day:
                timeline_items.append(
                    {
                        "time": "12:00",
                        "type": "check_out",
                        "title": "Otelden Cikis",
                        "notes": "Donus oncesi cikis islemleri.",
                    }
                )

            days.append(
                {
                    "day": day_no,
                    "timeline": timeline_items,
                }
            )

        options.append(
            {
                "plan_id": f"plan_{idx}_{uuid4().hex[:10]}",
                "title": f"Plan {'A' if idx == 1 else 'B'}",
                "gemini_recommendation": (
                    f"{city} icin {'aileye uygun ve dengeli' if idx == 1 else 'daha hareketli ve kesif odakli'} "
                    f"{total_days} gunluk plan onerisi."
                ),
                "summary": (
                    f"{total_days} Gun • {'Rahat tempo' if idx == 1 else 'Yogun tempo'}"
                ),
                "days": days,
                "estimated_total": 12400 if idx == 1 else 13800,
                "currency": currency,
            }
        )
    return options


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
    permission_classes = [permissions.IsAuthenticated]

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

        # Resolve hotel name for Gemini context
        hotel_name = ''
        hotel_reservation_id = payload.get("hotel_reservation_id")
        if hotel_reservation_id:
            hotel_res = HotelReservation.objects.filter(uuid=hotel_reservation_id).select_related('hotel').first()
            if hotel_res:
                hotel_name = hotel_res.hotel.name

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
                language=normalize_lang(payload.get("language")),
                family_mode=payload.get("family_mode", False),
                hotel_name=hotel_name,
                selected_tours=selected_tours_detail,
            )
        except Exception as e:
            print(f"CRITICAL GEMINI ERROR: {e}")
            options = build_plan_options(
                start_d,
                end_d,
                payload["city"],
                activities=payload.get("activities"),
                selected_tours=selected_tours_detail,
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
                "hotel_reservation_id": str(payload["hotel_reservation_id"]),
                "selected_tour_ids": [str(x) for x in payload.get("selected_tour_ids", [])],
                "language": payload["language"],
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
