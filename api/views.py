from django.contrib.auth import authenticate
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from api.serializers import RegisterSerializer, TravelPlanSerializer
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
        return Response({'status': 'ok', 'service': 'turquaway-backend'})


class TokenResponseSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()


class ErrorResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()


class LoginRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class RegisterView(APIView):
    @extend_schema(
        tags=['Auth'],
        summary='Register a new user',
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(response=TokenResponseSerializer, description='JWT tokens on success.'),
            400: OpenApiResponse(response=ErrorResponseSerializer, description='Validation error.'),
        },
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {'access_token': str(refresh.access_token), 'refresh_token': str(refresh)},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    @extend_schema(
        tags=['Auth'],
        summary='Login with email and password',
        request=LoginRequestSerializer,
        responses={
            200: OpenApiResponse(response=TokenResponseSerializer, description='JWT tokens on success.'),
            401: OpenApiResponse(response=ErrorResponseSerializer, description='Invalid credentials.'),
        },
    )
    def post(self, request):
        serializer = LoginRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
        )
        if user is None:
            return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        return Response(
            {'access_token': str(refresh.access_token), 'refresh_token': str(refresh)},
            status=status.HTTP_200_OK,
        )


class SuggestCitiesRequestSerializer(serializers.Serializer):
    budget_type = serializers.ChoiceField(choices=['luxury', 'economy', 'cheap'])
    activities = serializers.ListField(child=serializers.CharField(), allow_empty=False)


class SuggestCitiesResponseSerializer(serializers.Serializer):
    city = serializers.CharField()
    country = serializers.CharField()
    reason = serializers.CharField(required=False, allow_blank=True)


class GeneratePlanRequestSerializer(serializers.Serializer):
    city = serializers.CharField(max_length=150)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    adults = serializers.IntegerField(min_value=1)
    children = serializers.IntegerField(min_value=0, required=False, default=0)
    guests = serializers.IntegerField(min_value=1, required=False)
    budget_type = serializers.ChoiceField(choices=['luxury', 'economy', 'cheap'])
    activities = serializers.ListField(child=serializers.CharField(), allow_empty=False)

    def validate(self, attrs):
        if attrs['end_date'] < attrs['start_date']:
            raise serializers.ValidationError({'end_date': 'End date cannot be earlier than start date.'})

        adults = attrs['adults']
        children = attrs['children']
        guests = attrs.get('guests')
        if guests is not None and guests != adults + children:
            raise serializers.ValidationError({'guests': 'guests must equal adults + children.'})

        attrs['guests'] = adults + children
        return attrs


class GeneratePlanResponseSerializer(serializers.Serializer):
    itinerary_data = serializers.JSONField()


class SuggestCitiesView(APIView):
    @extend_schema(
        operation_id='suggest_cities',
        tags=['AI Travel'],
        summary='Suggest cities with Gemini',
        description='Returns exactly 3 city suggestions based on budget and activities.',
        request=SuggestCitiesRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=SuggestCitiesResponseSerializer(many=True),
                description='List of 3 suggested cities.',
            ),
            400: OpenApiResponse(response=ErrorResponseSerializer, description='Validation error.'),
            502: OpenApiResponse(response=ErrorResponseSerializer, description='Gemini upstream error.'),
        },
    )
    def post(self, request):
        serializer = SuggestCitiesRequestSerializer(data=request.data)
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
        description='Generates a structured itinerary with Gemini and stores it in TravelPlan.',
        request=GeneratePlanRequestSerializer,
        responses={
            200: OpenApiResponse(response=GeneratePlanResponseSerializer, description='Itinerary generated.'),
            400: OpenApiResponse(response=ErrorResponseSerializer, description='Validation error.'),
            502: OpenApiResponse(response=ErrorResponseSerializer, description='Gemini upstream error.'),
        },
    )
    def post(self, request):
        request_serializer = GeneratePlanRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        payload = request_serializer.validated_data

        adults = payload['adults']
        children = payload['children']

        try:
            service = GeminiService()
            itinerary_data = service.create_detailed_plan(
                city=payload['city'],
                start_date=payload['start_date'].isoformat(),
                end_date=payload['end_date'].isoformat(),
                adults=adults,
                children=children,
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
                'adults': adults,
                'children': children,
                'itinerary_data': itinerary_data,
            }
        )
        plan_serializer.is_valid(raise_exception=True)
        plan_serializer.save()

        return Response({'itinerary_data': itinerary_data}, status=status.HTTP_200_OK)
