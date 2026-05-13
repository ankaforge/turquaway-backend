from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from api.icon_utils import normalize_activity_icon_name
from api.models import (
	ActivityCategory,
	Destination,
	FunnelDraft,
	Hotel,
	HotelReservation,
	PartnerCompany,
	Tour,
	TourSession,
	TourReservation,
	TravelPlan,
	User,
	UserLegalConsent,
)


admin.site.site_header = 'Turquaway Yonetim Paneli'
admin.site.site_title = 'Turquaway Yonetim Paneli'
admin.site.index_title = 'Turquaway Yonetim Paneline Hos Geldiniz'


class ActivityCategoryAdminForm(forms.ModelForm):
	class Meta:
		model = ActivityCategory
		fields = '__all__'

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['icon'].help_text = 'Lucide React Native ikon adini girin. Ornek: ShipWheel, Camera, Landmark.'

	def clean_icon(self):
		return normalize_activity_icon_name(self.cleaned_data.get('icon'))


@admin.register(User)
class UserAdmin(BaseUserAdmin):
	ordering = ('id',)
	list_display = ('id', 'uuid', 'email', 'full_name', 'role', 'phone', 'country', 'language', 'is_staff', 'is_active')
	list_filter = ('role', 'is_staff', 'is_superuser', 'is_active', 'language', 'country')
	search_fields = ('email', 'full_name', 'phone', 'uuid')
	fieldsets = (
		(None, {'fields': ('email', 'password')}),
		(
			'Kullanici Bilgileri',
			{'fields': ('uuid', 'role', 'full_name', 'phone', 'country', 'language')},
		),
		('Izinler', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
		('Zaman Bilgisi', {'fields': ('last_login', 'date_joined')}),
	)
	readonly_fields = ('uuid', 'date_joined', 'last_login')
	add_fieldsets = (
		(
			None,
			{
				'classes': ('wide',),
				'fields': ('email', 'role', 'full_name', 'phone', 'country', 'language', 'password1', 'password2'),
			},
		),
	)


@admin.register(PartnerCompany)
class PartnerCompanyAdmin(admin.ModelAdmin):
	list_display = ('id', 'company_name', 'user', 'tax_number', 'commission_rate', 'is_approved', 'created_at')
	list_filter = ('is_approved',)
	search_fields = ('company_name', 'tax_number', 'user__email')
	autocomplete_fields = ('user',)


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
	list_display = ('id', 'name', 'active')
	list_filter = ('active',)
	search_fields = ('name',)


@admin.register(UserLegalConsent)
class UserLegalConsentAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'terms_accepted', 'privacy_accepted', 'version', 'accepted_at')
	list_filter = ('terms_accepted', 'privacy_accepted', 'version')
	search_fields = ('user__email', 'user__full_name', 'version')
	autocomplete_fields = ('user',)


@admin.register(FunnelDraft)
class FunnelDraftAdmin(admin.ModelAdmin):
	list_display = ('id', 'uuid', 'user', 'destination', 'start_date', 'end_date', 'adults', 'children', 'budget_type', 'updated_at')
	list_filter = ('budget_type', 'language')
	search_fields = ('user__email', 'user__full_name', 'uuid')
	autocomplete_fields = ('user', 'destination')
	readonly_fields = ('uuid', 'updated_at')


@admin.register(ActivityCategory)
class ActivityCategoryAdmin(admin.ModelAdmin):
	form = ActivityCategoryAdminForm
	list_display = ('id', 'key', 'name_tr', 'name_en', 'name_ru', 'name_ar', 'icon', 'active')
	list_filter = ('active',)
	search_fields = ('key', 'name_tr', 'name_en', 'name_ru', 'name_ar')


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
	list_display = (
		'id',
		'uuid',
		'name',
		'destination',
		'nightly_price_per_person',
		'currency',
		'rating',
		'sponsored',
		'family_friendly',
	)
	list_filter = ('destination', 'currency', 'sponsored', 'family_friendly')
	search_fields = ('name', 'destination__name', 'external_hotel_id', 'uuid')
	autocomplete_fields = ('destination',)
	readonly_fields = ('uuid',)


@admin.register(HotelReservation)
class HotelReservationAdmin(admin.ModelAdmin):
	list_display = ('id', 'uuid', 'user', 'hotel', 'start_date', 'end_date', 'adults', 'children', 'status')
	list_filter = ('status',)
	search_fields = ('uuid', 'user__email', 'hotel__name', 'payment_intent_id')
	autocomplete_fields = ('user', 'hotel')
	readonly_fields = ('uuid',)


@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
	list_display = ('id', 'uuid', 'title', 'provider', 'destination', 'price_adult', 'price_child', 'currency', 'family_friendly', 'is_approved')
	list_filter = ('destination', 'currency', 'family_friendly', 'is_approved', 'categories')
	search_fields = ('title', 'destination__name', 'provider__company_name', 'uuid')
	autocomplete_fields = ('provider', 'destination')
	readonly_fields = ('uuid',)
	filter_horizontal = ('categories',)


@admin.register(TourSession)
class TourSessionAdmin(admin.ModelAdmin):
	list_display = ('id', 'tour', 'date', 'start_time', 'end_time', 'capacity', 'booked_count', 'is_active')
	list_filter = ('is_active', 'date')
	search_fields = ('tour__title', 'tour__provider__company_name')
	autocomplete_fields = ('tour',)


@admin.register(TourReservation)
class TourReservationAdmin(admin.ModelAdmin):
	list_display = ('id', 'uuid', 'user', 'session', 'adults', 'children', 'total_price', 'status')
	list_filter = ('status',)
	search_fields = ('uuid', 'user__email', 'session__tour__title')
	autocomplete_fields = ('user', 'session', 'hotel_reservation')
	readonly_fields = ('uuid',)


@admin.register(TravelPlan)
class TravelPlanAdmin(admin.ModelAdmin):
	list_display = ('id', 'uuid', 'user', 'destination', 'status', 'confirmed_plan_id', 'created_at')
	list_filter = ('status',)
	search_fields = ('uuid', 'user__email', 'confirmed_plan_id')
	autocomplete_fields = ('user', 'destination')
	readonly_fields = ('uuid', 'created_at')
