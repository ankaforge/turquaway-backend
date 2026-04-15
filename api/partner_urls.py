from django.urls import path

from api import partner_views


urlpatterns = [
    path('login/', partner_views.partner_login_view, name='partner-login'),
    path('logout/', partner_views.partner_logout_view, name='partner-logout'),
    path('', partner_views.partner_dashboard_view, name='partner-dashboard'),
    path('company/', partner_views.partner_company_edit_view, name='partner-company-edit'),
    path('tours/new/', partner_views.partner_tour_create_view, name='partner-tour-create'),
    path('tours/<uuid:tour_uuid>/edit/', partner_views.partner_tour_edit_view, name='partner-tour-edit'),
    path('tours/<uuid:tour_uuid>/sessions/', partner_views.partner_tour_sessions_view, name='partner-tour-sessions'),
    path('tours/<uuid:tour_uuid>/sessions/<int:session_id>/reservations/', partner_views.partner_session_reservations_view, name='partner-session-reservations'),
]
