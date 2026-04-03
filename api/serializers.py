from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from api.models import (
    ActivityCategory,
    Destination,
    FunnelDraft,
    Hotel,
    HotelReservation,
    Tour,
    TourSession,
    TravelPlan,
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
        return attrs


class ActivityListItemSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = ActivityCategory
        fields = ['key', 'name', 'icon', 'active']

    def get_name(self, obj):
        lang = self.context.get('lang', 'en')
        if lang == 'tr':
            return obj.name_tr
        if lang == 'ru':
            return obj.name_ru
        if lang == 'ar':
            return obj.name_ar
        return obj.name_en


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


class PlanGenerateOptionsSerializer(serializers.Serializer):
    city = serializers.CharField(max_length=120)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    adults = serializers.IntegerField(min_value=1)
    children = serializers.IntegerField(min_value=0)
    budget_type = serializers.ChoiceField(choices=['luxury', 'economy', 'cheap'])
    activities = serializers.ListField(child=serializers.CharField(), allow_empty=False)
    hotel_reservation_id = serializers.UUIDField()
    selected_tour_ids = serializers.ListField(child=serializers.UUIDField(), required=False, default=list)
    language = serializers.ChoiceField(choices=['tr', 'en', 'ru', 'ar'], default='en')
    family_mode = serializers.BooleanField()

    def validate(self, attrs):
        if attrs['end_date'] < attrs['start_date']:
            raise serializers.ValidationError({'end_date': 'End date cannot be earlier than start date.'})
        if attrs['children'] > 0 and attrs['family_mode'] is not True:
            raise serializers.ValidationError({'family_mode': 'Must be true when children > 0.'})
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


class TourListItemSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='uuid')
    distance_km = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    provider = serializers.SerializerMethodField()

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
        ]

    def get_distance_km(self, obj):
        return 0

    def get_categories(self, obj):
        return list(obj.categories.values_list('key', flat=True))

    def get_provider(self, obj):
        if not obj.provider:
            return {'id': '', 'name': ''}
        return {'id': str(obj.provider_id), 'name': obj.provider.company_name}


class TravelPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelPlan
        fields = ['uuid', 'source_payload', 'options_payload', 'confirmed_plan_id', 'status']


class HotelReservationSerializer(serializers.ModelSerializer):
    payment_provider = serializers.SerializerMethodField()

    class Meta:
        model = HotelReservation
        fields = ['uuid', 'status', 'payment_provider', 'payment_intent_id']

    def get_payment_provider(self, obj):
        return 'booking_demand_partner'