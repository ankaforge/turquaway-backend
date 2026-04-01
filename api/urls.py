from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from api.views import GeneratePlanView, HealthCheckView, LoginView, RegisterView, SuggestCitiesView


urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='health-check'),
    # Auth
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='auth-token-refresh'),
    # AI Travel
    path('suggest-cities/', SuggestCitiesView.as_view(), name='suggest-cities'),
    path('generate-plan/', GeneratePlanView.as_view(), name='generate-plan'),
]