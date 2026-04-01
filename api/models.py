from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
	def create_user(self, email, password=None, **extra_fields):
		if not email:
			raise ValueError('Email is required.')
		email = self.normalize_email(email)
		user = self.model(email=email, **extra_fields)
		user.set_password(password)
		user.save(using=self._db)
		return user

	def create_superuser(self, email, password=None, **extra_fields):
		extra_fields.setdefault('is_staff', True)
		extra_fields.setdefault('is_superuser', True)
		return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
	full_name = models.CharField(max_length=255)
	email = models.EmailField(unique=True)
	phone = models.CharField(max_length=20, blank=True)
	country = models.CharField(max_length=2, blank=True)  # ISO 3166-1 alpha-2
	is_active = models.BooleanField(default=True)
	is_staff = models.BooleanField(default=False)
	date_joined = models.DateTimeField(auto_now_add=True)

	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = ['full_name']

	objects = UserManager()

	def __str__(self):
		return self.email


class TravelPlan(models.Model):
	class BudgetType(models.TextChoices):
		LUXURY = 'luxury', 'Luxury'
		ECONOMY = 'economy', 'Economy'
		CHEAP = 'cheap', 'Cheap'

	user = models.ForeignKey(
		'api.User',
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
	adults = models.PositiveIntegerField(default=1)
	children = models.PositiveIntegerField(default=0)
	itinerary_data = models.JSONField(default=dict, blank=True)

	def __str__(self):
		return f'{self.city} ({self.start_date} - {self.end_date})'
