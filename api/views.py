from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import serializers
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import TravelPlanSerializer
from api.utils import GeminiService


class HealthCheckSerializer(serializers.Serializer):
	status = serializers.CharField(help_text='Current health state of the API.')
	service = serializers.CharField(help_text='Service identifier returned by the backend.')


class HealthCheckView(APIView):
	@extend_schema(
		tags=['Health'],
		summary='Health check',
		description='Returns a simple status payload to confirm the API is reachable.',
		responses={200: HealthCheckSerializer},
	)
	def get(self, request):
		return Response({'status': 'ok', 'service': 'travel-turkey-backend'})


class SuggestCitiesRequestSerializer(serializers.Serializer):
	budget_type = serializers.ChoiceField(choices=['luxury', 'economy', 'cheap'])
	activities = serializers.ListField(
		child=serializers.CharField(),
		allow_empty=False,
	)


class SuggestCitiesResponseSerializer(serializers.Serializer):
	city = serializers.CharField()
	country = serializers.CharField()
	reason = serializers.CharField()


class GeneratePlanRequestSerializer(serializers.Serializer):
	city = serializers.CharField(max_length=150)
	start_date = serializers.DateField()
	end_date = serializers.DateField()
	guests = serializers.IntegerField(min_value=1)
	budget_type = serializers.ChoiceField(choices=['luxury', 'economy', 'cheap'])
	activities = serializers.ListField(
		child=serializers.CharField(),
		allow_empty=False,
	)

	def validate(self, attrs):
		if attrs['end_date'] < attrs['start_date']:
			raise serializers.ValidationError(
				{'end_date': 'End date cannot be earlier than start date.'}
			)
		return attrs


class GeneratePlanResponseSerializer(serializers.Serializer):
	travel_plan = TravelPlanSerializer()
	itinerary = serializers.JSONField()


class ErrorResponseSerializer(serializers.Serializer):
	detail = serializers.CharField()


class SuggestCitiesView(APIView):
	@extend_schema(
		operation_id='suggest_cities',
		tags=['AI Travel'],
		summary='Suggest cities with Gemini',
		description='Returns 3-5 city suggestions based on budget and activities.',
		request=SuggestCitiesRequestSerializer,
		responses={
			200: OpenApiResponse(
				response=SuggestCitiesResponseSerializer(many=True),
				description='List of suggested cities.',
			),
			400: OpenApiResponse(
				response=ErrorResponseSerializer,
				description='Validation error or Gemini JSON parsing error.',
			),
			502: OpenApiResponse(
				response=ErrorResponseSerializer,
				description='Gemini upstream/service error.',
			),
		},
		examples=[
			OpenApiExample(
				name='Suggest Cities Request',
				value={
					'budget_type': 'economy',
					'activities': ['historical places', 'local food', 'nature walks'],
				},
				request_only=True,
			),
			OpenApiExample(
				name='Suggest Cities Success',
				value=[
					{
						'city': 'Istanbul',
						'country': 'Turkey',
						'reason': 'Rich history, easy transport, and varied budget options.',
					},
					{
						'city': 'Prague',
						'country': 'Czech Republic',
						'reason': 'Great architecture and affordable food and transport.',
					},
					{
						'city': 'Tbilisi',
						'country': 'Georgia',
						'reason': 'Budget-friendly city with great cuisine and day trips.',
					},
				],
				response_only=True,
				status_codes=['200'],
			),
			OpenApiExample(
				name='Suggest Cities Error',
				value={'detail': 'Gemini should return between 3 and 5 city suggestions.'},
				response_only=True,
				status_codes=['400'],
			),
		],
	)
	def post(self, request):
		serializer = SuggestCitiesRequestSerializer(data=request.data)
		if not serializer.is_valid():
			print(f'[DEBUG] SuggestCitiesView validation errors: {serializer.errors}')
		serializer.is_valid(raise_exception=True)

		try:
			service = GeminiService()
			suggestions = service.get_city_suggestions(
				budget=serializer.validated_data['budget_type'],
				activities=serializer.validated_data['activities'],
			)
		except ValueError as exc:
			return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
		except Exception as exc:
			print(f'[ERROR] SuggestCitiesView Gemini failure: {exc}')
			return Response(
				{'detail': 'Failed to get city suggestions from Gemini.'},
				status=status.HTTP_502_BAD_GATEWAY,
			)

		return Response(suggestions, status=status.HTTP_200_OK)


class GeneratePlanView(APIView):
	@extend_schema(
		operation_id='generate_detailed_plan',
		tags=['AI Travel'],
		summary='Generate detailed travel plan',
		description='Generates a detailed travel plan with Gemini and stores it in TravelPlan.',
		request=GeneratePlanRequestSerializer,
		responses={
			201: OpenApiResponse(
				response=GeneratePlanResponseSerializer,
				description='Travel plan generated and saved successfully.',
			),
			400: OpenApiResponse(
				response=ErrorResponseSerializer,
				description='Validation error or Gemini JSON parsing error.',
			),
			502: OpenApiResponse(
				response=ErrorResponseSerializer,
				description='Gemini upstream/service error.',
			),
		},
		examples=[
			OpenApiExample(
				name='Generate Plan Request',
				value={
					'city': 'Istanbul',
					'start_date': '2026-04-10',
					'end_date': '2026-04-15',
					'guests': 2,
					'budget_type': 'economy',
					'activities': ['museum', 'food tour', 'boat trip'],
				},
				request_only=True,
			),
			OpenApiExample(
				name='Generate Plan Success',
				value={
					'travel_plan': {
						'id': 12,
						'user': None,
						'budget_type': 'economy',
						'activities': ['museum', 'food tour', 'boat trip'],
						'city': 'Istanbul',
						'start_date': '2026-04-10',
						'end_date': '2026-04-15',
						'guests': 2,
						'itinerary_data': {
							'daily_itinerary': [
								{'day': 1, 'morning': 'Old City walk', 'afternoon': 'Topkapi visit', 'evening': 'Galata dinner'}
							],
							'hotel_recommendations': [],
							'food_recommendations': [],
						},
					},
					'itinerary': {
						'city': 'Istanbul',
						'daily_itinerary': [
							{'day': 1, 'morning': 'Old City walk', 'afternoon': 'Topkapi visit', 'evening': 'Galata dinner'}
						],
					},
				},
				response_only=True,
				status_codes=['201'],
			),
			OpenApiExample(
				name='Generate Plan Validation Error',
				value={'detail': 'Failed to generate detailed plan from Gemini.'},
				response_only=True,
				status_codes=['502'],
			),
		],
	)
	def post(self, request):
		request_serializer = GeneratePlanRequestSerializer(data=request.data)
		request_serializer.is_valid(raise_exception=True)
		payload = request_serializer.validated_data

		try:
			service = GeminiService()
			itinerary_data = service.create_detailed_plan(
				city=payload['city'],
				dates={
					'start_date': payload['start_date'].isoformat(),
					'end_date': payload['end_date'].isoformat(),
				},
				guests=payload['guests'],
				budget=payload['budget_type'],
				activities=payload['activities'],
			)
		except ValueError as exc:
			return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
		except Exception as exc:
			print(f'[ERROR] GeneratePlanView Gemini failure: {exc}')
			return Response(
				{'detail': 'Failed to generate detailed plan from Gemini.'},
				status=status.HTTP_502_BAD_GATEWAY,
			)

		plan_serializer = TravelPlanSerializer(
			data={
				'user': request.user.id if request.user.is_authenticated else None,
				'budget_type': payload['budget_type'],
				'activities': payload['activities'],
				'city': payload['city'],
				'start_date': payload['start_date'],
				'end_date': payload['end_date'],
				'guests': payload['guests'],
				'itinerary_data': itinerary_data,
			}
		)
		plan_serializer.is_valid(raise_exception=True)
		travel_plan = plan_serializer.save()

		response_payload = {
			'travel_plan': TravelPlanSerializer(travel_plan).data,
			'itinerary': itinerary_data,
		}
		return Response(response_payload, status=status.HTTP_201_CREATED)
