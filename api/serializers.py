from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers
import re

from api.icon_utils import normalize_activity_icon_name
from api.models import (
    ActivityCategory,
    Destination,
    FunnelDraft,
    Hotel,
    HotelReservation,
    Tour,
    TourSession,
    TravelPlan,
    ReservationReview,
    User,
)

VALID_COUNTRY_CODES = {
    'AF','AX','AL','DZ','AS','AD','AO','AI','AQ','AG','AR','AM','AW','AU','AT',
    'AZ','BS','BH','BD','BB','BY','BE','BZ','BJ','BM','BT','BO','BQ','BA','BW',
    'BV','BR','IO','BN','BG','BF','BI','CV','KH','CM','CA','KY','CF','TD','CL',
    'CN','CX','CC','CO','KM','CG','CD','CK','CR','CI','HR','CU','CW','CY','CZ',
    'DK','DJ','DM','DO','EC','EG','SV','GQ','ER','EE','SZ','ET','FK','FO','FJ',
    'FI','FR','GF','PF','TF','GA','GM','GE','DE','GH','GI','GR','GL','GD','GP',
    'GU','GT','GG','GN','GW','GY','HT','HM','VA','HN','HK','HU','IS','IN','ID',
    'IR','IQ','IE','IM','IL','IT','JM','JP','JE','JO','KZ','KE','KI','KP','KR',
    'KW','KG','LA','LV','LB','LS','LR','LY','LI','LT','LU','MO','MG','MW','MY',
    'MV','ML','MT','MH','MQ','MR','MU','YT','MX','FM','MD','MC','MN','ME','MS',
    'MA','MZ','MM','NA','NR','NP','NL','NC','NZ','NI','NE','NG','NU','NF','MK',
    'MP','NO','OM','PK','PW','PS','PA','PG','PY','PE','PH','PN','PL','PT','PR',
    'QA','RE','RO','RU','RW','BL','SH','KN','LC','MF','PM','VC','WS','SM','ST',
    'SA','SN','RS','SC','SL','SG','SX','SK','SI','SB','SO','ZA','GS','SS','ES',
    'LK','SD','SR','SJ','SE','CH','SY','TW','TJ','TZ','TH','TL','TG','TK','TO',
    'TT','TN','TR','TM','TC','TV','UG','UA','AE','GB','US','UM','UY','UZ','VU',
    'VE','VN','VG','VI','WF','EH','YE','ZM','ZW',
}

def resolve_active_activity_keys(raw_values):
    active_keys = list(ActivityCategory.objects.filter(active=True).values_list('key', flat=True))
    key_map = {str(key).strip().lower(): key for key in active_keys}

    resolved = []
    invalid = []
    for value in raw_values or []:
        raw = str(value or '').strip()
        if not raw:
            invalid.append(raw)
            continue

        lookup = raw.lower()
        db_key = key_map.get(lookup)
        if not db_key:
            invalid.append(raw)
            continue

        if db_key not in resolved:
            resolved.append(db_key)

    return resolved, invalid


def activity_validation_message(invalid, valid_keys):
    invalid_text = ', '.join(invalid)
    valid_text = ', '.join(valid_keys) if valid_keys else 'none'
    return f"Unknown activity keys: {invalid_text}. Allowed keys: {valid_text}"


class RegisterSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20)
    country = serializers.CharField(max_length=2)
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    language = serializers.ChoiceField(choices=['tr', 'en', 'ru', 'ar'], default='en')
    consents = serializers.DictField()

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value.lower()

    def validate_country(self, value):
        if value.upper() not in VALID_COUNTRY_CODES:
            raise serializers.ValidationError('Enter a valid 2-letter ISO 3166-1 alpha-2 country code.')
        return value.upper()

    def validate_password(self, value):
        if value.isdigit():
            raise serializers.ValidationError('Password must not be entirely numeric.')
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': ['Passwords do not match.']})

        consents = attrs.get('consents', {})
        if not consents.get('terms_accepted'):
            raise serializers.ValidationError({'consents': {'terms_accepted': ['Must be true.']}})
        if not consents.get('privacy_accepted'):
            raise serializers.ValidationError({'consents': {'privacy_accepted': ['Must be true.']}})
        if not consents.get('accepted_at'):
            raise serializers.ValidationError({'consents': {'accepted_at': ['This field is required.']}})
        if not consents.get('version'):
            raise serializers.ValidationError({'consents': {'version': ['This field is required.']}})

        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm', None)
        validated_data.pop('consents', None)
        return User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            full_name=validated_data['full_name'],
            phone=validated_data['phone'],
            country=validated_data['country'],
            language=validated_data.get('language', 'en'),
        )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class RefreshTokenInputSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class MeLanguageSerializer(serializers.Serializer):
    language = serializers.ChoiceField(choices=['tr', 'en', 'ru', 'ar'])


class MeProfileUpdateSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=20)
    country = serializers.CharField(max_length=2)

    def validate_country(self, value):
        if value.upper() not in VALID_COUNTRY_CODES:
            raise serializers.ValidationError('Enter a valid 2-letter ISO 3166-1 alpha-2 country code.')
        return value.upper()

    def validate_phone(self, value):
        if not re.fullmatch(r'^\+?[0-9]{10,15}$', value or ''):
            raise serializers.ValidationError('Enter a valid phone number.')
        return value


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user is None or not user.check_password(attrs['current_password']):
            raise serializers.ValidationError({'current_password': ['Current password is incorrect.']})

        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': ['Passwords do not match.']})

        try:
            validate_password(attrs['new_password'], user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'new_password': list(exc.messages)})

        return attrs


class ReservationReviewCreateSerializer(serializers.Serializer):
    reservation_id = serializers.UUIDField()
    rating = serializers.IntegerField(min_value=1, max_value=5)
    feedback = serializers.CharField(allow_blank=True, required=False, default='')


class ReservationReviewSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='uuid')
    reservation_id = serializers.SerializerMethodField()

    class Meta:
        model = ReservationReview
        fields = ['id', 'reservation_id', 'rating', 'feedback', 'created_at']

    def get_reservation_id(self, obj):
        if obj.hotel_reservation_id:
            return str(obj.hotel_reservation.uuid)
        if obj.tour_reservation_id:
            return str(obj.tour_reservation.uuid)
        return ''


class FunnelDraftSerializer(serializers.ModelSerializer):
    class Meta:
        model = FunnelDraft
        fields = [
            'start_date',
            'end_date',
            'adults',
            'children',
            'budget_type',
            'activities',
            'language',
        ]

    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError(
                {'end_date': 'End date cannot be earlier than start date.'}
            )
        if attrs.get('adults', 0) < 1:
            raise serializers.ValidationError({'adults': 'adults must be at least 1.'})

        requested = attrs.get('activities') or []
        resolved, invalid = resolve_active_activity_keys(requested)
        if invalid:
            valid_keys = list(ActivityCategory.objects.filter(active=True).order_by('key').values_list('key', flat=True))
            raise serializers.ValidationError(
                {'activities': [activity_validation_message(invalid, valid_keys)]}
            )
        attrs['activities'] = resolved
        return attrs


class ActivityListItemSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    slug = serializers.CharField(source='key', read_only=True)
    icon = serializers.SerializerMethodField()

    class Meta:
        model = ActivityCategory
        fields = ['key', 'slug', 'name', 'icon', 'active']

    def get_name(self, obj):
        lang = self.context.get('lang', 'en')
        if lang == 'tr':
            return obj.name_tr
        if lang == 'ru':
            return obj.name_ru
        if lang == 'ar':
            return obj.name_ar
        return obj.name_en

    def get_icon(self, obj):
        return normalize_activity_icon_name(obj.icon)


class SuggestCitiesSerializer(serializers.Serializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    adults = serializers.IntegerField(min_value=1)
    children = serializers.IntegerField(min_value=0)
    budget_type = serializers.ChoiceField(choices=['luxury', 'economy', 'cheap'])
    activities = serializers.ListField(child=serializers.CharField(), allow_empty=False)
    language = serializers.ChoiceField(choices=['tr', 'en', 'ru', 'ar'], default='en')
    family_mode = serializers.BooleanField()

    def validate(self, attrs):
        if attrs['end_date'] < attrs['start_date']:
            raise serializers.ValidationError({'end_date': 'End date cannot be earlier than start date.'})
        if attrs['children'] > 0 and attrs['family_mode'] is not True:
            raise serializers.ValidationError({'family_mode': 'Must be true when children > 0.'})

        requested = attrs.get('activities') or []
        resolved, invalid = resolve_active_activity_keys(requested)
        if invalid:
            valid_keys = list(ActivityCategory.objects.filter(active=True).order_by('key').values_list('key', flat=True))
            raise serializers.ValidationError(
                {'activities': [activity_validation_message(invalid, valid_keys)]}
            )
        attrs['activities'] = resolved
        return attrs


class HotelSearchSerializer(serializers.Serializer):
    city = serializers.CharField(max_length=120)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    adults = serializers.IntegerField(min_value=1)
    children = serializers.IntegerField(min_value=0)
    budget_type = serializers.ChoiceField(choices=['luxury', 'economy', 'cheap'])
    activities = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    language = serializers.ChoiceField(choices=['tr', 'en', 'ru', 'ar'], default='en')
    sort = serializers.ChoiceField(choices=['price_asc', 'price_desc', 'value_score'], default='price_asc')

    def validate_activities(self, value):
        resolved, invalid = resolve_active_activity_keys(value or [])
        if invalid:
            valid_keys = list(ActivityCategory.objects.filter(active=True).order_by('key').values_list('key', flat=True))
            raise serializers.ValidationError(activity_validation_message(invalid, valid_keys))
        return resolved


class HotelReservationCreateSerializer(serializers.Serializer):
    hotel_id = serializers.UUIDField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    adults = serializers.IntegerField(min_value=1)
    children = serializers.IntegerField(min_value=0)
    guest_contact = serializers.DictField()

    def validate(self, attrs):
        if attrs['end_date'] < attrs['start_date']:
            raise serializers.ValidationError({'end_date': 'End date cannot be earlier than start date.'})
        return attrs


class HotelReservationWebhookSerializer(serializers.Serializer):
    event = serializers.ChoiceField(
        choices=['payment_succeeded', 'payment_failed', 'booking_confirmed', 'booking_cancelled']
    )
    payment_intent_id = serializers.CharField()


class TourSearchSerializer(serializers.Serializer):
    hotel_id = serializers.UUIDField()
    city = serializers.CharField(max_length=120)
    adults = serializers.IntegerField(min_value=1)
    children = serializers.IntegerField(min_value=0)
    budget_type = serializers.ChoiceField(choices=['luxury', 'economy', 'cheap'])
    activities = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    radius_km = serializers.IntegerField(min_value=1, default=30)
    language = serializers.ChoiceField(choices=['tr', 'en', 'ru', 'ar'], default='en')

    def validate_activities(self, value):
        resolved, invalid = resolve_active_activity_keys(value or [])
        if invalid:
            valid_keys = list(ActivityCategory.objects.filter(active=True).order_by('key').values_list('key', flat=True))
            raise serializers.ValidationError(activity_validation_message(invalid, valid_keys))
        return resolved


class PlanGenerateOptionsSerializer(serializers.Serializer):
    city = serializers.CharField(max_length=120)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    adults = serializers.IntegerField(min_value=1)
    children = serializers.IntegerField(min_value=0)
    budget_type = serializers.ChoiceField(choices=['luxury', 'economy', 'cheap'])
    activities = serializers.ListField(child=serializers.CharField(), allow_empty=False)
    hotel_reservation_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    selected_tour_ids = serializers.ListField(child=serializers.UUIDField(), required=False, default=list)
    language = serializers.ChoiceField(choices=['tr', 'en', 'ru', 'ar'], default='en')
    family_mode = serializers.BooleanField()

    def validate(self, attrs):
        if attrs['end_date'] < attrs['start_date']:
            raise serializers.ValidationError({'end_date': 'End date cannot be earlier than start date.'})
        if attrs['children'] > 0 and attrs['family_mode'] is not True:
            raise serializers.ValidationError({'family_mode': 'Must be true when children > 0.'})

        requested = attrs.get('activities') or []
        resolved, invalid = resolve_active_activity_keys(requested)
        if invalid:
            valid_keys = list(ActivityCategory.objects.filter(active=True).order_by('key').values_list('key', flat=True))
            raise serializers.ValidationError(
                {'activities': [activity_validation_message(invalid, valid_keys)]}
            )
        if not resolved:
            raise serializers.ValidationError({'activities': ['At least one valid activity is required.']})

        attrs['activities'] = resolved
        return attrs


class PlanConfirmSerializer(serializers.Serializer):
    plan_id = serializers.CharField(max_length=64)


class HotelListItemSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='uuid')
    city = serializers.SerializerMethodField()
    sponsored_badge = serializers.SerializerMethodField()
    distance_to_center_km = serializers.SerializerMethodField()

    class Meta:
        model = Hotel
        fields = [
            'id',
            'name',
            'city',
            'nightly_price_per_person',
            'currency',
            'rating',
            'sponsored',
            'sponsored_badge',
            'family_friendly',
            'distance_to_center_km',
            'image',
        ]

    def get_sponsored_badge(self, obj):
        return 'Gemini Onerisi' if obj.sponsored else ''

    def get_city(self, obj):
        return obj.destination.name if obj.destination else ''

    def get_distance_to_center_km(self, obj):
        return 0


class TourSessionSlotSerializer(serializers.ModelSerializer):
    session_id = serializers.IntegerField(source='id')
    available_spots = serializers.SerializerMethodField()

    class Meta:
        model = TourSession
        fields = ['session_id', 'date', 'start_time', 'end_time', 'capacity', 'available_spots', 'is_active']

    def get_available_spots(self, obj):
        return max(obj.capacity - obj.booked_count, 0)


class TourListItemSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='uuid')
    distance_km = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    provider = serializers.SerializerMethodField()
    available_sessions = serializers.SerializerMethodField()
    services = serializers.SerializerMethodField()

    class Meta:
        model = Tour
        fields = [
            'id',
            'title',
            'description',
            'price_adult',
            'price_child',
            'currency',
            'distance_km',
            'family_friendly',
            'categories',
            'provider',
            'location_link',
            'services',
            'available_sessions',
        ]

    def get_distance_km(self, obj):
        return 0

    def get_categories(self, obj):
        return list(obj.categories.values_list('key', flat=True))

    def get_provider(self, obj):
        if not obj.provider:
            return {'id': '', 'name': ''}
        return {'id': str(obj.provider_id), 'name': obj.provider.company_name}

    def get_services(self, obj):
        return {
            'free_food_drinks': obj.includes_free_food_drinks,
            'hotel_pickup_dropoff': obj.includes_hotel_pickup_dropoff,
        }

    def get_available_sessions(self, obj):
        from django.utils import timezone
        today = timezone.localdate()
        sessions = (
            obj.sessions
            .filter(is_active=True, date__gte=today)
            .order_by('date', 'start_time')[:10]
        )
        return TourSessionSlotSerializer(sessions, many=True).data


class TourReservationCreateSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()
    adults = serializers.IntegerField(min_value=1)
    children = serializers.IntegerField(min_value=0, default=0)
    hotel_reservation_id = serializers.UUIDField(required=False, allow_null=True, default=None)

    def validate_session_id(self, value):
        from django.utils import timezone
        try:
            session = TourSession.objects.select_related('tour').get(pk=value)
        except TourSession.DoesNotExist:
            raise serializers.ValidationError('Session not found.')
        if not session.is_active:
            raise serializers.ValidationError('This session is not active.')
        if session.date < timezone.localdate():
            raise serializers.ValidationError('This session is in the past.')
        if not session.tour or not session.tour.is_approved:
            raise serializers.ValidationError('Tour is not available.')
        self._session = session
        return value

    def validate(self, attrs):
        session: TourSession = getattr(self, '_session', None)
        if session is None:
            return attrs
        adults = attrs['adults']
        children = attrs.get('children', 0)
        available = session.capacity - session.booked_count
        if adults + children > available:
            raise serializers.ValidationError(
                {'session_id': f'Not enough spots. Available: {available}.'}
            )
        return attrs


class TravelPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelPlan
        fields = ['uuid', 'source_payload', 'options_payload', 'confirmed_plan_id', 'status']


class TravelPlanListItemSerializer(serializers.ModelSerializer):
    plan_id = serializers.UUIDField(source='uuid')
    city = serializers.SerializerMethodField()
    start_date = serializers.SerializerMethodField()
    end_date = serializers.SerializerMethodField()
    gemini_recommendation = serializers.SerializerMethodField()
    days = serializers.SerializerMethodField()

    class Meta:
        model = TravelPlan
        fields = [
            'plan_id',
            'city',
            'status',
            'start_date',
            'end_date',
            'gemini_recommendation',
            'days',
        ]

    def _selected_option(self, obj):
        options = obj.options_payload or []
        if not options:
            return {}

        selected = next(
            (item for item in options if item.get('plan_id') == obj.confirmed_plan_id),
            None,
        )
        return selected or options[0]

    def get_city(self, obj):
        return obj.source_payload.get('city') or (obj.destination.name if obj.destination else '')

    def get_start_date(self, obj):
        return obj.source_payload.get('start_date')

    def get_end_date(self, obj):
        return obj.source_payload.get('end_date')

    def get_gemini_recommendation(self, obj):
        return self._selected_option(obj).get('gemini_recommendation')

    def get_days(self, obj):
        return self._selected_option(obj).get('days', [])


class HotelReservationSerializer(serializers.ModelSerializer):
    payment_provider = serializers.SerializerMethodField()

    class Meta:
        model = HotelReservation
        fields = ['uuid', 'status', 'payment_provider', 'payment_intent_id']

    def get_payment_provider(self, obj):
        return 'booking_demand_partner'