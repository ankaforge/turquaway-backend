from django.conf import settings
from django.db import models


class TravelPlan(models.Model):
	class BudgetType(models.TextChoices):
		LUXURY = 'luxury', 'Luxury'
		ECONOMY = 'economy', 'Economy'
		CHEAP = 'cheap', 'Cheap'

	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='travel_plans',
	)
	budget_type = models.CharField(max_length=20, choices=BudgetType.choices)
	activities = models.JSONField(default=list, blank=True)
	city = models.CharField(max_length=150)
	start_date = models.DateField()
	end_date = models.DateField()
	guests = models.PositiveIntegerField()
	itinerary_data = models.JSONField(default=dict, blank=True)

	def __str__(self):
		return f'{self.city} ({self.start_date} - {self.end_date})'
