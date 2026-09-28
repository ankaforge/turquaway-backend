import logging
from datetime import date

from celery import Task, shared_task
from django.db import transaction

from api.models import HotelReservation, Tour, TravelPlan
from api.services.gemini_facade import GeminiService

logger = logging.getLogger(__name__)


class PlanGenerationTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        if args:
            TravelPlan.objects.filter(
                uuid=args[0],
                generation_status=TravelPlan.GenerationStatus.PROCESSING,
            ).update(
                generation_status=TravelPlan.GenerationStatus.FAILED,
                generation_error='Plan generation failed. Please try again.',
            )
        logger.error('Plan generation task failed: %s', exc)


@shared_task(bind=True, base=PlanGenerationTask, max_retries=0)
def generate_plan_options_task(self, plan_uuid: str) -> None:
    with transaction.atomic():
        plan = (
            TravelPlan.objects.select_for_update()
            .select_related('user')
            .get(uuid=plan_uuid)
        )
        is_redelivery = (self.request.delivery_info or {}).get('redelivered', False)
        if plan.generation_status != TravelPlan.GenerationStatus.PENDING and not (
            plan.generation_status == TravelPlan.GenerationStatus.PROCESSING and is_redelivery
        ):
            return
        plan.generation_status = TravelPlan.GenerationStatus.PROCESSING
        plan.save(update_fields=['generation_status'])
        payload = plan.source_payload

    start_date = date.fromisoformat(payload['start_date'])
    end_date = date.fromisoformat(payload['end_date'])
    hotel_name = payload.get('hotel_name', '')
    hotel_lat = None
    hotel_lng = None
    hotel_reservation_id = payload.get('hotel_reservation_id')
    if hotel_reservation_id:
        hotel_reservation = HotelReservation.objects.filter(
            uuid=hotel_reservation_id,
            user_id=plan.user_id,
        ).select_related('hotel').first()
        if hotel_reservation:
            hotel_name = hotel_reservation.hotel.name
            hotel_lat = hotel_reservation.hotel.lat
            hotel_lng = hotel_reservation.hotel.lng

    candidate_partner_tours = []
    partner_tours = Tour.objects.filter(
        destination__name__iexact=payload['city'],
        is_approved=True,
    )
    activity_keys = payload.get('activities') or []
    if activity_keys:
        partner_tours = partner_tours.filter(categories__key__in=activity_keys).distinct()
    for tour in partner_tours.select_related('destination', 'provider__user').order_by('title')[:40]:
        candidate_partner_tours.append({
            'title': tour.title,
            'category': tour.categories.values_list('key', flat=True).first() or 'general',
            'area': tour.destination.name if tour.destination else payload['city'],
            'price_level': payload.get('budget_type', 'economy'),
            'provider_name': tour.provider.company_name if tour.provider else '',
            'phone': str(tour.provider.user.phone or '').strip() if tour.provider else '',
            'website': tour.location_link or '',
        })

    selected_tours = []
    selected_tour_ids = payload.get('selected_tour_ids') or []
    for tour in Tour.objects.filter(uuid__in=selected_tour_ids).prefetch_related('sessions'):
        session = (
            tour.sessions.filter(is_active=True, date__range=(start_date, end_date))
            .order_by('date', 'start_time')
            .first()
        )
        selected_tours.append({
            'title': tour.title,
            'session_date': session.date.isoformat() if session else None,
            'start_time': session.start_time.strftime('%H:%M') if session else None,
            'end_time': session.end_time.strftime('%H:%M') if session else None,
            'includes_food': tour.includes_free_food_drinks,
            'includes_transfer': tour.includes_hotel_pickup_dropoff,
        })

    try:
        options = GeminiService().generate_plan_options(
            city=payload['city'],
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            budget=payload['budget_type'],
            activities=payload['activities'],
            adults=payload['adults'],
            children=payload['children'],
            language=payload['language'],
            family_mode=payload['family_mode'],
            hotel_name=hotel_name,
            hotel_lat=hotel_lat,
            hotel_lng=hotel_lng,
            selected_tours=selected_tours,
            partner_tours=candidate_partner_tours,
        )
        from api.views import _is_valid_options_payload

        if not _is_valid_options_payload(options):
            raise ValueError('AI provider returned an invalid options payload.')
    except Exception:
        logger.exception('AI plan generation failed for plan %s', plan_uuid)
        try:
            from api.views import build_plan_options

            options = build_plan_options(
                start_date,
                end_date,
                payload['city'],
                activities=payload.get('activities'),
                selected_tours=selected_tours,
                language=payload.get('language', 'en'),
                hotel_name=hotel_name,
            )
        except Exception:
            logger.exception('Fallback plan generation failed for plan %s', plan_uuid)
            TravelPlan.objects.filter(pk=plan.pk).update(
                generation_status=TravelPlan.GenerationStatus.FAILED,
                generation_error='Plan generation failed. Please try again.',
            )
            return

    TravelPlan.objects.filter(pk=plan.pk).update(
        options_payload=options,
        generation_status=TravelPlan.GenerationStatus.COMPLETED,
        generation_error='',
    )