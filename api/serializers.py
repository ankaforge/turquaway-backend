import re

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from api.models import TravelPlan, User

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
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True, default='')
    country = serializers.CharField(max_length=2, required=False, allow_blank=True, default='')
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value.lower()

    def validate_country(self, value):
        if value and value.upper() not in VALID_COUNTRY_CODES:
            raise serializers.ValidationError('Enter a valid 2-letter ISO 3166-1 alpha-2 country code.')
        return value.upper() if value else value

    def validate_password(self, value):
        if value.isdigit():
            raise serializers.ValidationError('Password must not be entirely numeric.')
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            full_name=validated_data['full_name'],
            phone=validated_data.get('phone', ''),
            country=validated_data.get('country', ''),
        )


class TravelPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelPlan
        fields = [
            'id',
            'user',
            'budget_type',
            'activities',
            'city',
            'start_date',
            'end_date',
            'guests',
            'adults',
            'children',
            'itinerary_data',
        ]
        extra_kwargs = {
            'user': {'required': False, 'allow_null': True},
        }

    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError(
                {'end_date': 'End date cannot be earlier than start date.'}
            )

        adults = attrs.get('adults', 1)
        children = attrs.get('children', 0)
        guests = attrs.get('guests')
        if guests is not None and guests != adults + children:
            raise serializers.ValidationError(
                {'guests': 'guests must equal adults + children.'}
            )

        return attrs


class TravelPlanSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelPlan
        fields = ['id', 'city', 'budget_type', 'start_date', 'end_date', 'guests', 'adults', 'children']