from uuid import uuid4
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.db.models import Q

# ---------------------------------------------------------
# 1. KULLANICI VE AUTH SİSTEMİ
# ---------------------------------------------------------
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
    class Role(models.TextChoices):
        CUSTOMER = 'customer', 'Customer'
        PARTNER = 'partner', 'Tour Partner'
        ADMIN = 'admin', 'Admin'

    uuid = models.UUIDField(default=uuid4, db_index=True, editable=False)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, default='')
    country = models.CharField(max_length=2, default='')  
    language = models.CharField(max_length=2, default='en')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']
    objects = UserManager()

    def __str__(self):
        return self.email

class UserLegalConsent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='legal_consents')
    terms_accepted = models.BooleanField(default=False)
    privacy_accepted = models.BooleanField(default=False)
    accepted_at = models.DateTimeField()
    version = models.CharField(max_length=20, default='v1')
    created_at = models.DateTimeField(auto_now_add=True)

# ---------------------------------------------------------
# 2. B2B PARTNER (TUR ŞİRKETLERİ PANELİ İÇİN)
# ---------------------------------------------------------
class PartnerCompany(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='partner_profile')
    company_name = models.CharField(max_length=150)
    tax_number = models.CharField(max_length=50)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00) # %10 komisyon vs.
    is_approved = models.BooleanField(default=False) # Merkezden onaylanmadan panel açılmaz
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.company_name

# ---------------------------------------------------------
# 3. DESTİNASYON VE KATEGORİLER (CORE VERİLER)
# ---------------------------------------------------------
class Destination(models.Model):
    name = models.CharField(max_length=120, unique=True) # Örn: Antalya, Mersin
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class ActivityCategory(models.Model):
    key = models.CharField(max_length=50, unique=True)
    name_tr = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    name_ru = models.CharField(max_length=100)
    name_ar = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default='sparkles')
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.key

# ---------------------------------------------------------
# 4. SATIN ALMA HUNİSİ (FUNNEL)
# ---------------------------------------------------------
class FunnelDraft(models.Model):
    class BudgetType(models.TextChoices):
        LUXURY = 'luxury', 'Luxury'
        ECONOMY = 'economy', 'Economy'
        CHEAP = 'cheap', 'Cheap'

    uuid = models.UUIDField(default=uuid4, unique=True, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='funnel_draft')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    adults = models.PositiveIntegerField(default=1)
    children = models.PositiveIntegerField(default=0)
    budget_type = models.CharField(max_length=20, choices=BudgetType.choices)
    activities = models.JSONField(default=list, blank=True) # Seçilen kategori key'leri
    language = models.CharField(max_length=2, default='en')
    destination = models.ForeignKey(Destination, on_delete=models.SET_NULL, null=True, blank=True) # String yerine model ilişkisi
    updated_at = models.DateTimeField(auto_now=True)

# ---------------------------------------------------------
# 5. OTEL VE OTEL REZERVASYONU
# ---------------------------------------------------------
class Hotel(models.Model):
    uuid = models.UUIDField(default=uuid4, unique=True, editable=False)
    external_hotel_id = models.CharField(max_length=100, blank=True) # Booking API ID
    name = models.CharField(max_length=150)
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='hotels', null=True, blank=True)
    lat = models.FloatField(default=0.0) # Mesafe hesaplamak için ZORUNLU
    lng = models.FloatField(default=0.0) # Mesafe hesaplamak için ZORUNLU
    nightly_price_per_person = models.PositiveIntegerField()
    currency = models.CharField(max_length=5, default='TRY')
    rating = models.FloatField(default=0)
    sponsored = models.BooleanField(default=False)
    family_friendly = models.BooleanField(default=True)
    image = models.URLField(blank=True)

class HotelReservation(models.Model):
    class Status(models.TextChoices):
        PENDING_PAYMENT = 'pending_payment', 'Pending payment'
        PAYMENT_SUCCEEDED = 'payment_succeeded', 'Payment succeeded'
        BOOKING_CONFIRMED = 'booking_confirmed', 'Booking confirmed'
        BOOKING_CANCELLED = 'booking_cancelled', 'Booking cancelled'

    uuid = models.UUIDField(default=uuid4, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hotel_reservations')
    hotel = models.ForeignKey(Hotel, on_delete=models.PROTECT, related_name='reservations')
    start_date = models.DateField()
    end_date = models.DateField()
    adults = models.PositiveIntegerField(default=1)
    children = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING_PAYMENT)
    payment_intent_id = models.CharField(max_length=100, blank=True)

# ---------------------------------------------------------
# 6. B2B TURLAR, SEANSLAR VE REZERVASYONLAR
# ---------------------------------------------------------
class Tour(models.Model):
    uuid = models.UUIDField(default=uuid4, unique=True, editable=False)
    provider = models.ForeignKey(PartnerCompany, on_delete=models.CASCADE, related_name='tours', null=True, blank=True) # Gerçek B2B bağlantısı
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='tours', null=True, blank=True)
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    location_link = models.URLField(blank=True)
    lat = models.FloatField(default=0)
    lng = models.FloatField(default=0)
    price_adult = models.PositiveIntegerField(default=0)
    price_child = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=5, default='TRY')
    family_friendly = models.BooleanField(default=True)
    includes_free_food_drinks = models.BooleanField(default=False)
    includes_hotel_pickup_dropoff = models.BooleanField(default=False)
    categories = models.ManyToManyField(ActivityCategory, related_name='tours')
    is_approved = models.BooleanField(default=False) # Turquaway Admin Onayı

class TourSession(models.Model):
    # Bu model sayesinde kapasite, saat ve takvim yönetimi yapabiliriz
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='sessions', null=True, blank=True)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    capacity = models.PositiveIntegerField()
    booked_count = models.PositiveIntegerField(default=0) # Doluluk oranı takibi
    is_active = models.BooleanField(default=True) # Hava kötüyse şirket kapatabilsin

class TourReservation(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed' # Müşteri geldi, tahsilat yapıldı
        NO_SHOW = 'no_show', 'No Show' # Müşteri gelmedi
        CANCELLED = 'cancelled', 'Cancelled'

    uuid = models.UUIDField(default=uuid4, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tour_reservations')
    session = models.ForeignKey(TourSession, on_delete=models.PROTECT, related_name='reservations', null=True, blank=True) # Artık tura değil, spesifik bir saate bağlanıyor
    hotel_reservation = models.ForeignKey(HotelReservation, on_delete=models.SET_NULL, null=True, blank=True)
    adults = models.PositiveIntegerField(default=1)
    children = models.PositiveIntegerField(default=0)
    total_price = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING)

# ---------------------------------------------------------
# 7. YAPAY ZEKA SEYAHAT PLANI
# ---------------------------------------------------------
class TravelPlan(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        CONFIRMED = 'confirmed', 'Confirmed'
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'

    uuid = models.UUIDField(default=uuid4, db_index=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='travel_plans', null=True, blank=True)
    destination = models.ForeignKey(Destination, on_delete=models.SET_NULL, null=True)
    source_payload = models.JSONField(default=dict, blank=True)
    options_payload = models.JSONField(default=list, blank=True)
    confirmed_plan_id = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(default=timezone.now)


class ReservationReview(models.Model):
    uuid = models.UUIDField(default=uuid4, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservation_reviews')
    hotel_reservation = models.ForeignKey(HotelReservation, on_delete=models.CASCADE, null=True, blank=True, related_name='reviews')
    tour_reservation = models.ForeignKey(TourReservation, on_delete=models.CASCADE, null=True, blank=True, related_name='reviews')
    rating = models.PositiveSmallIntegerField()
    feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'hotel_reservation'],
                condition=Q(hotel_reservation__isnull=False),
                name='unique_user_hotel_review',
            ),
            models.UniqueConstraint(
                fields=['user', 'tour_reservation'],
                condition=Q(tour_reservation__isnull=False),
                name='unique_user_tour_review',
            ),
        ]