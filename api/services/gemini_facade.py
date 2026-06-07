from typing import Any, Dict, List

from api.services.openai_client import OpenAIJsonClient
from api.services.plan_context import PlanContextService
from api.services.plan_generator import PlanGeneratorService
from api.services.plan_postprocess import PlanPostProcessor
from api.services.recommender import RecommenderService


class GeminiService:
    """Backward-compatible facade used by existing view code."""

    def __init__(self, model_name: str = "gpt-4o"):
        client = OpenAIJsonClient(model_name=model_name)
        context_service = PlanContextService(client)
        post_processor = PlanPostProcessor(context_service)

        self.client = client
        self.recommender = RecommenderService(client)
        self.context_service = context_service
        self.post_processor = post_processor
        self.plan_generator = PlanGeneratorService(client, context_service, post_processor)

    def get_city_suggestions(
        self,
        budget: str,
        activities: List[str],
        language: str = "en",
        allowed_destinations: List[str] | None = None,
    ) -> List[Dict[str, str]]:
        return self.recommender.get_city_suggestions(
            budget=budget,
            activities=activities,
            language=language,
            allowed_destinations=allowed_destinations,
        )

    def rank_hotels(
        self,
        hotels: List[Dict[str, Any]],
        budget: str,
        activities: List[str],
        language: str = "en",
    ) -> List[str]:
        return self.recommender.rank_hotels(
            hotels=hotels,
            budget=budget,
            activities=activities,
            language=language,
        )

    def rank_tours(
        self,
        tours: List[Dict[str, Any]],
        budget: str,
        activities: List[str],
        language: str = "en",
        family_mode: bool = False,
    ) -> List[str]:
        return self.recommender.rank_tours(
            tours=tours,
            budget=budget,
            activities=activities,
            language=language,
            family_mode=family_mode,
        )

    def generate_plan_options(
        self,
        city: str,
        start_date: str,
        end_date: str,
        budget: str,
        activities: List[str],
        adults: int = 1,
        children: int = 0,
        language: str = "en",
        family_mode: bool = False,
        hotel_name: str = "",
        hotel_lat: float | None = None,
        hotel_lng: float | None = None,
        selected_tours: List[Dict[str, Any]] | None = None,
        partner_tours: List[Dict[str, Any]] | None = None,
    ) -> List[Dict[str, Any]]:
        return self.plan_generator.generate_plan_options(
            city=city,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            activities=activities,
            adults=adults,
            children=children,
            language=language,
            family_mode=family_mode,
            hotel_name=hotel_name,
            hotel_lat=hotel_lat,
            hotel_lng=hotel_lng,
            selected_tours=selected_tours,
            partner_tours=partner_tours,
        )
