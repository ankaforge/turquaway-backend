from functools import wraps
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from api.forms import (
    PartnerCompanyForm,
    PartnerLoginForm,
    PartnerTourForm,
    RecurringTourSessionForm,
    TourSessionForm,
)
from api.models import PartnerCompany, Tour, TourSession, User


PARTNER_HOME_NAME = 'partner-dashboard'


def partner_required(view_func):
    @wraps(view_func)
    @login_required(login_url='partner-login')
    def _wrapped(request, *args, **kwargs):
        if request.user.role != User.Role.PARTNER:
            return HttpResponseForbidden('Bu alan sadece partner kullanicilar icindir.')
        return view_func(request, *args, **kwargs)

    return _wrapped


def partner_login_view(request):
    if request.user.is_authenticated and request.user.role == User.Role.PARTNER:
        return redirect(PARTNER_HOME_NAME)

    form = PartnerLoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(request, username=email, password=password)

        if user is None or user.role != User.Role.PARTNER:
            messages.error(request, 'Kullanici bilgileri hatali veya yetkiniz yok.')
        else:
            login(request, user)
            return redirect(PARTNER_HOME_NAME)

    return render(request, 'partner/login.html', {'form': form})


@partner_required
def partner_logout_view(request):
    logout(request)
    return redirect('partner-login')


@partner_required
def partner_dashboard_view(request):
    company = PartnerCompany.objects.filter(user=request.user).first()
    tours = Tour.objects.filter(provider=company).select_related('destination').prefetch_related('sessions') if company else []

    total_sessions = 0
    for tour in tours:
        total_sessions += tour.sessions.count()

    context = {
        'company': company,
        'tours': tours,
        'pending_tour_count': sum(1 for tour in tours if not tour.is_approved),
        'tour_count': len(tours),
        'session_count': total_sessions,
    }
    return render(request, 'partner/dashboard.html', context)


@partner_required
def partner_company_edit_view(request):
    company = PartnerCompany.objects.filter(user=request.user).first()
    form = PartnerCompanyForm(request.POST or None, instance=company)

    if request.method == 'POST' and form.is_valid():
        company_obj = form.save(commit=False)
        company_obj.user = request.user
        if company is None:
            company_obj.is_approved = False
        company_obj.save()
        messages.success(request, 'Sirket bilgileri kaydedildi.')
        return redirect(PARTNER_HOME_NAME)

    return render(request, 'partner/company_form.html', {'form': form, 'company': company})


@partner_required
def partner_tour_create_view(request):
    company = PartnerCompany.objects.filter(user=request.user).first()
    if company is None:
        messages.warning(request, 'Once sirket bilgilerinizi kaydetmelisiniz.')
        return redirect('partner-company-edit')

    form = PartnerTourForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        tour = form.save(commit=False)
        tour.provider = company
        tour.is_approved = False
        tour.save()
        form.save_m2m()
        messages.success(request, 'Tur olusturuldu. Admin onayi bekleniyor.')
        return redirect(PARTNER_HOME_NAME)

    return render(request, 'partner/tour_form.html', {'form': form, 'tour': None})


@partner_required
def partner_tour_edit_view(request, tour_uuid):
    company = PartnerCompany.objects.filter(user=request.user).first()
    tour = get_object_or_404(Tour, uuid=tour_uuid, provider=company)

    form = PartnerTourForm(request.POST or None, instance=tour)
    if request.method == 'POST' and form.is_valid():
        edited = form.save(commit=False)
        edited.is_approved = False
        edited.save()
        form.save_m2m()
        messages.success(request, 'Tur guncellendi. Tekrar admin onayi gerekecek.')
        return redirect(PARTNER_HOME_NAME)

    return render(request, 'partner/tour_form.html', {'form': form, 'tour': tour})


@partner_required
def partner_tour_sessions_view(request, tour_uuid):
    company = PartnerCompany.objects.filter(user=request.user).first()
    tour = get_object_or_404(Tour, uuid=tour_uuid, provider=company)

    single_form = TourSessionForm()
    recurring_form = RecurringTourSessionForm()

    if request.method == 'POST':
        action = request.POST.get('action', 'single')

        if action == 'single':
            single_form = TourSessionForm(request.POST)
            if single_form.is_valid():
                session = single_form.save(commit=False)
                session.tour = tour
                session.save()
                messages.success(request, 'Tek seans eklendi.')
                return redirect('partner-tour-sessions', tour_uuid=tour.uuid)

        elif action == 'recurring':
            recurring_form = RecurringTourSessionForm(request.POST)
            if recurring_form.is_valid():
                start_date = recurring_form.cleaned_data['start_date']
                end_date = recurring_form.cleaned_data['end_date']
                weekdays = {int(day) for day in recurring_form.cleaned_data['weekdays']}
                start_time = recurring_form.cleaned_data['start_time']
                end_time = recurring_form.cleaned_data['end_time']
                capacity = recurring_form.cleaned_data['capacity']
                is_active = recurring_form.cleaned_data['is_active']

                created_count = 0
                skipped_count = 0
                current = start_date

                while current <= end_date:
                    if current.weekday() in weekdays:
                        _, created = TourSession.objects.get_or_create(
                            tour=tour,
                            date=current,
                            start_time=start_time,
                            end_time=end_time,
                            defaults={
                                'capacity': capacity,
                                'is_active': is_active,
                            },
                        )
                        if created:
                            created_count += 1
                        else:
                            skipped_count += 1
                    current += timedelta(days=1)

                if created_count:
                    messages.success(
                        request,
                        f'{created_count} adet tekrarlayan seans olusturuldu. '
                        f'{skipped_count} adet mevcut seans atlandi.' if skipped_count else f'{created_count} adet tekrarlayan seans olusturuldu.',
                    )
                else:
                    messages.warning(request, 'Yeni seans olusturulamadi. Secilen aralikta ayni saatte seanslar zaten mevcut.')

                return redirect('partner-tour-sessions', tour_uuid=tour.uuid)

    sessions = (
        TourSession.objects
        .filter(tour=tour)
        .prefetch_related('reservations__user', 'reservations__hotel_reservation__hotel')
        .order_by('date', 'start_time')
    )

    for session in sessions:
        session.available_spots = max(session.capacity - session.booked_count, 0)
        session.reservation_count = len(session.reservations.all())

    return render(
        request,
        'partner/tour_sessions.html',
        {
            'tour': tour,
            'single_form': single_form,
            'recurring_form': recurring_form,
            'sessions': sessions,
        },
    )


@partner_required
def partner_session_reservations_view(request, tour_uuid, session_id):
    company = PartnerCompany.objects.filter(user=request.user).first()
    tour = get_object_or_404(Tour, uuid=tour_uuid, provider=company)
    session = get_object_or_404(
        TourSession.objects.prefetch_related('reservations__user', 'reservations__hotel_reservation__hotel'),
        pk=session_id,
        tour=tour,
    )

    reservations = [
        {
            'reservation_id': str(reservation.uuid),
            'full_name': reservation.user.full_name,
            'email': reservation.user.email,
            'phone': reservation.user.phone,
            'hotel_name': reservation.hotel_reservation.hotel.name if reservation.hotel_reservation_id else '',
            'adults': reservation.adults,
            'children': reservation.children,
            'total_guests': reservation.adults + reservation.children,
            'status_label': reservation.get_status_display(),
        }
        for reservation in session.reservations.all()
    ]

    return render(
        request,
        'partner/session_reservations.html',
        {
            'tour': tour,
            'session': session,
            'reservations': reservations,
        },
    )
