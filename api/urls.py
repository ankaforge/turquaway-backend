from django.urls import path

from api.views import GeneratePlanView, HealthCheckView, SuggestCitiesView


urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('suggest-cities/', SuggestCitiesView.as_view(), name='suggest-cities'),
    path('generate-plan/', GeneratePlanView.as_view(), name='generate-plan'),
]