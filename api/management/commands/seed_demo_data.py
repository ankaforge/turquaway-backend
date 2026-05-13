from datetime import date, time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

from api.models import (
    ActivityCategory,
    Destination,
    FunnelDraft,
    Hotel,
    PartnerCompany,
    Tour,
    TourSession,
    User,
)


class Command(BaseCommand):
    help = "Seed demo activities, hotels, tours and sessions for backend testing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete previous demo data and reseed from scratch",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            self._reset_demo_data()

        destinations = self._seed_destinations()
        activities = self._seed_activities()
        partner = self._seed_partner_company()
        self._seed_hotels(destinations)
        self._seed_tours_and_sessions(destinations, activities, partner)
        self._seed_demo_funnel_for_customer(destinations, activities)

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))

    def _reset_demo_data(self):
        TourSession.objects.filter(tour__provider__user__email__in=["partner.demo@turquaway.local"]).delete()
        Tour.objects.filter(provider__user__email__in=["partner.demo@turquaway.local"]).delete()
        Hotel.objects.filter(external_hotel_id__startswith="demo_").delete()
        FunnelDraft.objects.filter(user__email="customer.demo@turquaway.local").delete()
        PartnerCompany.objects.filter(user__email="partner.demo@turquaway.local").delete()
        User.objects.filter(email__in=["partner.demo@turquaway.local", "customer.demo@turquaway.local"]).delete()
        Destination.objects.filter(name__in=["Antalya", "Mugla", "Nevsehir"]).delete()
        ActivityCategory.objects.filter(key__in=["safari", "diving", "boat", "culture", "nature"]).delete()

    def _seed_destinations(self):
        rows = [
            {
                "name": "Antalya",
                "description": "Popular coast destination with family friendly options.",
                "image_url": "https://images.unsplash.com/photo-1601581875309-fafbf2d3ed3a",
            },
            {
                "name": "Mugla",
                "description": "Bays, beaches and nature heavy routes.",
                "image_url": "https://images.unsplash.com/photo-1528127269322-539801943592",
            },
            {
                "name": "Nevsehir",
                "description": "Culture and landscape focused travel destination.",
                "image_url": "https://images.unsplash.com/photo-1603565816030-6b389eeb23cb",
            },
        ]

        by_name = {}
        for row in rows:
            obj, _ = Destination.objects.update_or_create(
                name=row["name"],
                defaults={
                    "description": row["description"],
                    "image_url": row["image_url"],
                    "active": True,
                },
            )
            by_name[obj.name] = obj

        return by_name

    def _seed_activities(self):
        rows = [
            {
                "key": "safari",
                "name_tr": "Safari",
                "name_en": "Safari",
                "name_ru": "Safari",
                "name_ar": "Safari",
                "icon": "Binoculars",
            },
            {
                "key": "diving",
                "name_tr": "Dalis",
                "name_en": "Diving",
                "name_ru": "Diving",
                "name_ar": "Diving",
                "icon": "Waves",
            },
            {
                "key": "boat",
                "name_tr": "Tekne",
                "name_en": "Boat",
                "name_ru": "Boat",
                "name_ar": "Boat",
                "icon": "ShipWheel",
            },
            {
                "key": "culture",
                "name_tr": "Kultur",
                "name_en": "Culture",
                "name_ru": "Culture",
                "name_ar": "Culture",
                "icon": "Landmark",
            },
            {
                "key": "nature",
                "name_tr": "Doga",
                "name_en": "Nature",
                "name_ru": "Nature",
                "name_ar": "Nature",
                "icon": "Trees",
            },
        ]

        by_key = {}
        for row in rows:
            obj, _ = ActivityCategory.objects.update_or_create(
                key=row["key"],
                defaults={
                    "name_tr": row["name_tr"],
                    "name_en": row["name_en"],
                    "name_ru": row["name_ru"],
                    "name_ar": row["name_ar"],
                    "icon": row["icon"],
                    "active": True,
                },
            )
            by_key[obj.key] = obj

        return by_key

    def _seed_partner_company(self):
        partner_user, _ = User.objects.update_or_create(
            email="partner.demo@turquaway.local",
            defaults={
                "full_name": "Demo Partner",
                "phone": "+905550000001",
                "country": "TR",
                "language": "tr",
                "role": User.Role.PARTNER,
                "is_active": True,
            },
        )
        if not partner_user.has_usable_password():
            partner_user.set_password("DemoPass123!")
            partner_user.save(update_fields=["password"])

        partner, _ = PartnerCompany.objects.update_or_create(
            user=partner_user,
            defaults={
                "company_name": "Blue Coast Tours",
                "tax_number": "TR1234567890",
                "commission_rate": 12.50,
                "is_approved": True,
            },
        )
        return partner

    def _seed_hotels(self, destinations):
        rows = [
            {
                "external_hotel_id": "demo_antalya_1",
                "name": "Antalya Seaside Hotel",
                "destination": destinations["Antalya"],
                "lat": 36.8841,
                "lng": 30.7056,
                "nightly_price_per_person": 4200,
                "currency": "TRY",
                "rating": 4.6,
                "sponsored": True,
                "family_friendly": True,
                "image": "https://images.unsplash.com/photo-1566073771259-6a8506099945",
            },
            {
                "external_hotel_id": "demo_mugla_1",
                "name": "Mugla Bay Resort",
                "destination": destinations["Mugla"],
                "lat": 36.7450,
                "lng": 28.2450,
                "nightly_price_per_person": 5600,
                "currency": "TRY",
                "rating": 4.4,
                "sponsored": False,
                "family_friendly": True,
                "image": "https://images.unsplash.com/photo-1496417263034-38ec4f0b665a",
            },
            {
                "external_hotel_id": "demo_nevsehir_1",
                "name": "Cappadocia Stone Hotel",
                "destination": destinations["Nevsehir"],
                "lat": 38.6250,
                "lng": 34.7120,
                "nightly_price_per_person": 7100,
                "currency": "TRY",
                "rating": 4.8,
                "sponsored": False,
                "family_friendly": True,
                "image": "https://images.unsplash.com/photo-1618773928121-c32242e63f39",
            },
        ]

        for row in rows:
            Hotel.objects.update_or_create(
                external_hotel_id=row["external_hotel_id"],
                defaults=row,
            )

    def _seed_tours_and_sessions(self, destinations, activities, partner):
        rows = [
            {
                "title": "Antalya Canyon Safari",
                "destination": destinations["Antalya"],
                "description": "Full day safari with canyon route and lunch.",
                "lat": 36.9120,
                "lng": 30.7300,
                "price_adult": 1800,
                "price_child": 900,
                "currency": "TRY",
                "family_friendly": True,
                "is_approved": True,
                "activity_keys": ["safari", "nature"],
            },
            {
                "title": "Mugla Blue Diving Day",
                "destination": destinations["Mugla"],
                "description": "Beginner friendly diving with safety equipment.",
                "lat": 36.7800,
                "lng": 28.2700,
                "price_adult": 2200,
                "price_child": 1100,
                "currency": "TRY",
                "family_friendly": True,
                "is_approved": True,
                "activity_keys": ["diving", "boat"],
            },
            {
                "title": "Nevsehir Culture and Valley Tour",
                "destination": destinations["Nevsehir"],
                "description": "Culture tour with valley viewpoints and local food.",
                "lat": 38.6400,
                "lng": 34.8200,
                "price_adult": 1600,
                "price_child": 800,
                "currency": "TRY",
                "family_friendly": True,
                "is_approved": True,
                "activity_keys": ["culture", "nature"],
            },
        ]

        for row in rows:
            activity_keys = row.pop("activity_keys")
            tour, _ = Tour.objects.update_or_create(
                provider=partner,
                title=row["title"],
                defaults={"provider": partner, **row},
            )
            tour.categories.set([activities[key] for key in activity_keys])

            start_date = date.today() + timedelta(days=1)
            for idx in range(3):
                TourSession.objects.update_or_create(
                    tour=tour,
                    date=start_date + timedelta(days=idx),
                    start_time=time(9 + idx, 0),
                    defaults={
                        "end_time": time(12 + idx, 0),
                        "capacity": 24,
                        "booked_count": 0,
                        "is_active": True,
                    },
                )

    def _seed_demo_funnel_for_customer(self, destinations, activities):
        customer, _ = User.objects.update_or_create(
            email="customer.demo@turquaway.local",
            defaults={
                "full_name": "Demo Customer",
                "phone": "+905550000002",
                "country": "TR",
                "language": "tr",
                "role": User.Role.CUSTOMER,
                "is_active": True,
            },
        )
        if not customer.has_usable_password():
            customer.set_password("DemoPass123!")
            customer.save(update_fields=["password"])

        FunnelDraft.objects.update_or_create(
            user=customer,
            defaults={
                "start_date": date.today() + timedelta(days=10),
                "end_date": date.today() + timedelta(days=13),
                "adults": 2,
                "children": 1,
                "budget_type": FunnelDraft.BudgetType.ECONOMY,
                "activities": [activities["safari"].key, activities["diving"].key],
                "language": "tr",
                "destination": destinations["Antalya"],
            },
        )
