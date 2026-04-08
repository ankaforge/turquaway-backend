from uuid import uuid4

from django.contrib.auth import authenticate
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
    ReservationReviewCreateSerializer,
    ReservationReviewSerializer,
    RefreshTokenInputSerializer,
    RegisterSerializer,
    SuggestCitiesSerializer,
    TourListItemSerializer,
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


def build_plan_options(start_date, end_date, city: str, currency: str = "TRY"):
    total_days = max((end_date - start_date).days + 1, 1)
    options = []
    for idx in [1, 2]:
        days = []
        for day_index in range(total_days):
            day_no = day_index + 1
            base_time = "09:00" if idx == 1 else "10:00"
            days.append(
                {
                    "day": day_no,
                    "timeline": [
                        {
                            "time": base_time,
                            "type": "activity",
                            "title": f"{city} Kesif Rotasi {day_no}",
                            "notes": "Aileye uygun" if idx == 1 else "Daha dinamik rota",
                        }
                    ],
                }
            )

        options.append(
            {
                "plan_id": f"plan_{idx}_{uuid4().hex[:10]}",
                "title": f"Plan {'A' if idx == 1 else 'B'}",
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
        try:
            options = GeminiService().generate_plan_options(
                city=payload["city"],
                start_date=payload["start_date"].isoformat(),
                end_date=payload["end_date"].isoformat(),
                budget=payload["budget_type"],
                activities=payload["activities"],
                language=normalize_lang(payload.get("language")),
                family_mode=payload.get("family_mode", False),
            )
        except Exception:
            options = build_plan_options(payload["start_date"], payload["end_date"], payload["city"])

        destination = Destination.objects.filter(name__iexact=payload["city"]).first()
        plan = TravelPlan.objects.create(
            user=request.user,
            destination=destination,
            source_payload={
                "city": payload["city"],
                "start_date": payload["start_date"].isoformat(),
                "end_date": payload["end_date"].isoformat(),
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

            tours = Tour.objects.filter(uuid__in=selected_tour_ids)
            for tour in tours:
                session = (
                    TourSession.objects.filter(tour=tour, is_active=True)
                    .order_by("date", "start_time")
                    .first()
                )
                if session is None:
                    continue
                TourReservation.objects.create(
                    user=request.user,
                    session=session,
                    hotel_reservation=hotel_reservation,
                    adults=travel_plan.source_payload.get("adults", 1),
                    children=travel_plan.source_payload.get("children", 0),
                    total_price=(
                        session.tour.price_adult * travel_plan.source_payload.get("adults", 1)
                        + session.tour.price_child * travel_plan.source_payload.get("children", 0)
                    ),
                    status=TourReservation.Status.CONFIRMED,
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


class PlanRestartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        FunnelDraft.objects.filter(user=request.user).delete()
        TravelPlan.objects.filter(user=request.user, status__in=[TravelPlan.Status.DRAFT, TravelPlan.Status.ACTIVE]).update(
            status=TravelPlan.Status.COMPLETED
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
