from rest_framework import serializers

from api.models import TravelPlan


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

        return attrs


class TravelPlanSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelPlan
        fields = ['id', 'city', 'budget_type', 'start_date', 'end_date', 'guests']