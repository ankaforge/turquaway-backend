from datetime import timedelta
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from api.models import (
	ActivityCategory,
	Destination,
	Hotel,
	HotelReservation,
	PartnerCompany,
	TravelPlan,
	Tour,
	TourReservation,
	TourSession,
	User,
)


class ActivityListViewTests(APITestCase):
	def test_activities_returns_slug_and_normalized_icon(self):
		ActivityCategory.objects.create(
			key='boat_tour',
			name_tr='Tekne Turu',
			name_en='Boat Tour',
			name_ru='Boat Tour',
			name_ar='Boat Tour',
			icon='ship-wheel',
			active=True,
		)

		response = self.client.get(reverse('activities') + '?lang=tr')

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['results'][0]['slug'], 'boat_tour')
		self.assertEqual(response.data['results'][0]['name'], 'Tekne Turu')
		self.assertEqual(response.data['results'][0]['icon'], 'ShipWheel')

	def test_activities_normalizes_custom_admin_icon_input(self):
		ActivityCategory.objects.create(
			key='custom_activity',
			name_tr='Ozel Aktivite',
			name_en='Custom Activity',
			name_ru='Custom Activity',
			name_ar='Custom Activity',
			icon='not-a-real-lucide-icon',
			active=True,
		)

		response = self.client.get(reverse('activities'))

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['results'][0]['icon'], 'NotARealLucideIcon')


class ProfileModuleTests(APITestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			email='ada@example.com',
			password='StrongPass123!',
			full_name='Ada Lovelace',
			phone='+905551112233',
			country='TR',
			language='tr',
		)

		refresh = RefreshToken.for_user(self.user)
		self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')

		self.destination = Destination.objects.create(name='Antalya', active=True)
		self.hotel = Hotel.objects.create(
			name='Hotel A',
			destination=self.destination,
			nightly_price_per_person=4200,
			currency='TRY',
			rating=4.5,
			sponsored=True,
			family_friendly=True,
		)

	def test_patch_me_updates_profile(self):
		url = reverse('me')
		payload = {
			'full_name': 'Ada Byron',
			'phone': '+905551119999',
			'country': 'TR',
		}

		response = self.client.patch(url, payload, format='json')

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.user.refresh_from_db()
		self.assertEqual(self.user.full_name, 'Ada Byron')
		self.assertEqual(self.user.phone, '+905551119999')

	def test_change_password_success(self):
		url = reverse('me-password')
		payload = {
			'current_password': 'StrongPass123!',
			'new_password': 'EvenStronger456!',
			'new_password_confirm': 'EvenStronger456!',
		}

		response = self.client.post(url, payload, format='json')

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.user.refresh_from_db()
		self.assertTrue(self.user.check_password('EvenStronger456!'))

	def test_list_hotel_reservations(self):
		HotelReservation.objects.create(
			user=self.user,
			hotel=self.hotel,
			start_date=timezone.localdate() + timedelta(days=2),
			end_date=timezone.localdate() + timedelta(days=5),
			adults=2,
			children=1,
			status=HotelReservation.Status.PENDING_PAYMENT,
		)

		response = self.client.get(reverse('me-reservations') + '?type=hotel')

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(response.data['results']), 1)
		self.assertIn(response.data['results'][0]['status'], ['active', 'completed', 'cancelled'])

	def test_list_tour_reservations(self):
		partner_user = User.objects.create_user(
			email='partner@example.com',
			password='PartnerPass123!',
			full_name='Partner User',
			phone='+905551110000',
			country='TR',
			role=User.Role.PARTNER,
		)
		partner = PartnerCompany.objects.create(
			user=partner_user,
			company_name='Partner Tour Co',
			tax_number='TR123',
			is_approved=True,
		)
		tour = Tour.objects.create(
			provider=partner,
			destination=self.destination,
			title='Canyon Safari',
			description='All day tour',
			price_adult=1000,
			price_child=500,
			is_approved=True,
		)
		session = TourSession.objects.create(
			tour=tour,
			date=timezone.localdate() - timedelta(days=1),
			start_time='09:00',
			end_time='12:00',
			capacity=20,
			booked_count=2,
			is_active=True,
		)
		TourReservation.objects.create(
			user=self.user,
			session=session,
			adults=2,
			children=0,
			total_price=2000,
			status=TourReservation.Status.CONFIRMED,
		)

		response = self.client.get(reverse('me-reservations') + '?type=tour')

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(response.data['results']), 1)
		self.assertEqual(response.data['results'][0]['title'], 'Canyon Safari')

	def test_voucher_endpoint_respects_ownership(self):
		own = HotelReservation.objects.create(
			user=self.user,
			hotel=self.hotel,
			start_date=timezone.localdate(),
			end_date=timezone.localdate() + timedelta(days=1),
		)
		other_user = User.objects.create_user(
			email='other@example.com',
			password='OtherPass123!',
			full_name='Other User',
			phone='+905551118888',
			country='TR',
		)
		other = HotelReservation.objects.create(
			user=other_user,
			hotel=self.hotel,
			start_date=timezone.localdate(),
			end_date=timezone.localdate() + timedelta(days=1),
		)

		ok_response = self.client.get(reverse('me-reservation-voucher', kwargs={'reservation_id': str(own.uuid)}))
		denied_response = self.client.get(reverse('me-reservation-voucher', kwargs={'reservation_id': str(other.uuid)}))

		self.assertEqual(ok_response.status_code, status.HTTP_200_OK)
		self.assertIn('.pdf', ok_response.data['url'])
		self.assertEqual(denied_response.status_code, status.HTTP_404_NOT_FOUND)

	def test_create_review_once_for_hotel_reservation(self):
		reservation = HotelReservation.objects.create(
			user=self.user,
			hotel=self.hotel,
			start_date=timezone.localdate() - timedelta(days=4),
			end_date=timezone.localdate() - timedelta(days=1),
			status=HotelReservation.Status.BOOKING_CONFIRMED,
		)
		url = reverse('me-reviews')
		payload = {
			'reservation_id': str(reservation.uuid),
			'rating': 5,
			'feedback': 'Harika bir deneyimdi.',
		}

		first = self.client.post(url, payload, format='json')
		second = self.client.post(url, payload, format='json')

		self.assertEqual(first.status_code, status.HTTP_201_CREATED)
		self.assertEqual(second.status_code, status.HTTP_409_CONFLICT)

	def test_same_user_cannot_create_second_reservation_for_same_session(self):
		partner_user = User.objects.create_user(
			email='partner-dup@example.com',
			password='PartnerPass123!',
			full_name='Partner Dup',
			phone='+905551115555',
			country='TR',
			role=User.Role.PARTNER,
		)
		partner = PartnerCompany.objects.create(
			user=partner_user,
			company_name='Duplicate Guard Co',
			tax_number='TR777',
			is_approved=True,
		)
		tour = Tour.objects.create(
			provider=partner,
			destination=self.destination,
			title='Morning Jeep Tour',
			description='Off-road tour',
			price_adult=800,
			price_child=400,
			is_approved=True,
		)
		session = TourSession.objects.create(
			tour=tour,
			date=timezone.localdate() + timedelta(days=5),
			start_time='09:00',
			end_time='11:00',
			capacity=15,
			booked_count=0,
			is_active=True,
		)

		payload = {
			'session_id': session.id,
			'adults': 2,
			'children': 1,
		}

		first = self.client.post(reverse('tour-reservation-create'), payload, format='json')
		second = self.client.post(reverse('tour-reservation-create'), payload, format='json')

		self.assertEqual(first.status_code, status.HTTP_201_CREATED)
		self.assertEqual(second.status_code, status.HTTP_409_CONFLICT)
		self.assertEqual(TourReservation.objects.filter(user=self.user, session=session).count(), 1)
		session.refresh_from_db()
		self.assertEqual(session.booked_count, 3)

	def test_list_plans_returns_all_non_draft_plans(self):
		ongoing_plan = TravelPlan.objects.create(
			user=self.user,
			destination=self.destination,
			source_payload={
				'city': 'Antalya',
				'start_date': (timezone.localdate() - timedelta(days=1)).isoformat(),
				'end_date': (timezone.localdate() + timedelta(days=2)).isoformat(),
			},
			options_payload=[
				{
					'plan_id': 'generated-1',
					'gemini_recommendation': 'Kemer ve Olimpos icin ideal bahar donemi.',
					'days': [
						{
							'day': 1,
							'timeline': [
								{
									'time': '09:00',
									'title': 'Konyaalti Plaji',
									'notes': 'Sabah erken gitmek tavsiye edilir.',
								}
							],
						}
					],
				}
			],
			confirmed_plan_id='generated-1',
			status=TravelPlan.Status.ACTIVE,
		)
		completed_plan = TravelPlan.objects.create(
			user=self.user,
			source_payload={
				'city': 'Istanbul',
				'start_date': (timezone.localdate() - timedelta(days=12)).isoformat(),
				'end_date': (timezone.localdate() - timedelta(days=9)).isoformat(),
			},
			options_payload=[
				{
					'plan_id': 'generated-2',
					'gemini_recommendation': None,
					'days': [],
				}
			],
			confirmed_plan_id='generated-2',
			status=TravelPlan.Status.COMPLETED,
		)
		TravelPlan.objects.create(
			user=self.user,
			source_payload={
				'city': 'Izmir',
				'start_date': (timezone.localdate() + timedelta(days=5)).isoformat(),
				'end_date': (timezone.localdate() + timedelta(days=7)).isoformat(),
			},
			status=TravelPlan.Status.DRAFT,
		)

		response = self.client.get(reverse('plans-list'))

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['count'], 2)
		self.assertEqual(len(response.data['results']), 2)
		self.assertEqual(response.data['results'][0]['plan_id'], str(completed_plan.uuid))
		self.assertEqual(response.data['results'][1]['plan_id'], str(ongoing_plan.uuid))
		self.assertEqual(response.data['results'][1]['city'], 'Antalya')
		self.assertEqual(response.data['results'][1]['status'], 'active')
		self.assertEqual(response.data['results'][1]['gemini_recommendation'], 'Kemer ve Olimpos icin ideal bahar donemi.')
		self.assertEqual(response.data['results'][1]['days'][0]['timeline'][0]['title'], 'Konyaalti Plaji')

	def test_list_plans_filters_by_temporal_status(self):
		TravelPlan.objects.create(
			user=self.user,
			source_payload={
				'city': 'Antalya',
				'start_date': (timezone.localdate() - timedelta(days=1)).isoformat(),
				'end_date': (timezone.localdate() + timedelta(days=1)).isoformat(),
			},
			options_payload=[{'plan_id': 'ongoing', 'days': []}],
			confirmed_plan_id='ongoing',
			status=TravelPlan.Status.ACTIVE,
		)
		TravelPlan.objects.create(
			user=self.user,
			source_payload={
				'city': 'Mugla',
				'start_date': (timezone.localdate() + timedelta(days=3)).isoformat(),
				'end_date': (timezone.localdate() + timedelta(days=6)).isoformat(),
			},
			options_payload=[{'plan_id': 'upcoming', 'days': []}],
			confirmed_plan_id='upcoming',
			status=TravelPlan.Status.ACTIVE,
		)
		TravelPlan.objects.create(
			user=self.user,
			source_payload={
				'city': 'Istanbul',
				'start_date': (timezone.localdate() - timedelta(days=8)).isoformat(),
				'end_date': (timezone.localdate() - timedelta(days=5)).isoformat(),
			},
			options_payload=[{'plan_id': 'past', 'days': []}],
			confirmed_plan_id='past',
			status=TravelPlan.Status.COMPLETED,
		)

		ongoing_response = self.client.get(reverse('plans-list') + '?status=ongoing')
		upcoming_response = self.client.get(reverse('plans-list') + '?status=upcoming')
		past_response = self.client.get(reverse('plans-list') + '?status=past')

		self.assertEqual(ongoing_response.status_code, status.HTTP_200_OK)
		self.assertEqual(upcoming_response.status_code, status.HTTP_200_OK)
		self.assertEqual(past_response.status_code, status.HTTP_200_OK)
		self.assertEqual(ongoing_response.data['count'], 1)
		self.assertEqual(ongoing_response.data['results'][0]['city'], 'Antalya')
		self.assertEqual(upcoming_response.data['count'], 1)
		self.assertEqual(upcoming_response.data['results'][0]['city'], 'Mugla')
		self.assertEqual(past_response.data['count'], 1)
		self.assertEqual(past_response.data['results'][0]['city'], 'Istanbul')


class PlanContractTests(APITestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			email='plan-user@example.com',
			password='StrongPass123!',
			full_name='Plan User',
			phone='+905551117777',
			country='TR',
			language='en',
		)

		refresh = RefreshToken.for_user(self.user)
		self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')

		self.destination = Destination.objects.create(name='Antalya', active=True)

	def _payload(self):
		return {
			'city': 'Antalya',
			'start_date': (timezone.localdate() + timedelta(days=2)).isoformat(),
			'end_date': (timezone.localdate() + timedelta(days=4)).isoformat(),
			'adults': 2,
			'children': 0,
			'budget_type': 'economy',
			'activities': ['culture', 'food'],
			'selected_tour_ids': [],
			'language': 'en',
			'family_mode': False,
		}

	def test_generate_options_accepts_missing_hotel_reservation_id(self):
		response = self.client.post(reverse('plans-generate-options'), self._payload(), format='json')

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIsInstance(response.data.get('options'), list)
		self.assertGreater(len(response.data['options']), 0)
		first_option = response.data['options'][0]
		self.assertIn('plan_id', first_option)
		self.assertIn('title', first_option)
		self.assertTrue('summary' in first_option or 'description' in first_option)
		self.assertIn('estimated_total', first_option)
		self.assertIn('currency', first_option)
		self.assertIsInstance(first_option.get('days'), list)

		plan = TravelPlan.objects.filter(user=self.user).latest('created_at')
		self.assertIsNone(plan.source_payload.get('hotel_reservation_id'))

	def test_generate_options_activities_empty_returns_field_error(self):
		payload = self._payload()
		payload['activities'] = []

		response = self.client.post(reverse('plans-generate-options'), payload, format='json')

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertEqual(response.data['code'], 'validation_error')
		self.assertIn('activities', response.data['fields'])

	def test_generate_options_invalid_date_format_returns_field_error(self):
		payload = self._payload()
		payload['start_date'] = '06/07/2026'

		response = self.client.post(reverse('plans-generate-options'), payload, format='json')

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertEqual(response.data['code'], 'validation_error')
		self.assertIn('start_date', response.data['fields'])

	@patch('api.views.GeminiService.generate_plan_options', return_value=[])
	def test_generate_options_falls_back_when_ai_returns_empty(self, _mock_generate):
		response = self.client.post(reverse('plans-generate-options'), self._payload(), format='json')

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIsInstance(response.data.get('options'), list)
		self.assertGreater(len(response.data['options']), 0)
		self.assertIn('days', response.data['options'][0])

	def test_current_plan_returns_plan_city_and_days_timeline(self):
		TravelPlan.objects.create(
			user=self.user,
			destination=self.destination,
			source_payload={'city': 'Antalya'},
			options_payload=[
				{
					'plan_id': 'contract-plan-1',
					'title': 'Plan',
					'summary': 'Summary',
					'estimated_total': 1000,
					'currency': 'TRY',
					'days': [
						{
							'day': 1,
							'timeline': [
								{
									'time': '09:00',
									'type': 'activity',
									'title': 'Old Town Walk',
									'notes': 'Visit old town area.',
								}
							],
						},
					],
				},
			],
			confirmed_plan_id='contract-plan-1',
			status=TravelPlan.Status.ACTIVE,
		)

		response = self.client.get(reverse('plans-current'))

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['plan_id'], 'contract-plan-1')
		self.assertEqual(response.data['city'], 'Antalya')
		self.assertIsInstance(response.data['days'], list)
		self.assertIsInstance(response.data['days'][0]['timeline'], list)


class PartnerSessionViewTests(APITestCase):
	def test_partner_sees_reservation_link_on_session_page(self):
		partner_user = User.objects.create_user(
			email='partner2@example.com',
			password='PartnerPass123!',
			full_name='Partner User 2',
			phone='+905551110001',
			country='TR',
			role=User.Role.PARTNER,
		)
		company = PartnerCompany.objects.create(
			user=partner_user,
			company_name='Session Partner Co',
			tax_number='TR999',
			is_approved=True,
		)
		destination = Destination.objects.create(name='Mersin', active=True)
		tour = Tour.objects.create(
			provider=company,
			destination=destination,
			title='Boat Session',
			description='Boat tour session',
			price_adult=900,
			price_child=450,
			is_approved=True,
		)
		session = TourSession.objects.create(
			tour=tour,
			date=timezone.localdate() + timedelta(days=2),
			start_time='10:00',
			end_time='12:00',
			capacity=10,
			booked_count=3,
			is_active=True,
		)
		customer = User.objects.create_user(
			email='guest@example.com',
			password='StrongPass123!',
			full_name='Test Guest',
			phone='+905551113333',
			country='TR',
		)
		hotel = Hotel.objects.create(
			name='Seaside Resort',
			destination=destination,
			nightly_price_per_person=3500,
			currency='TRY',
			rating=4.7,
			family_friendly=True,
		)
		hotel_reservation = HotelReservation.objects.create(
			user=customer,
			hotel=hotel,
			start_date=timezone.localdate() + timedelta(days=1),
			end_date=timezone.localdate() + timedelta(days=4),
			adults=2,
			children=1,
			status=HotelReservation.Status.BOOKING_CONFIRMED,
		)
		TourReservation.objects.create(
			user=customer,
			session=session,
			hotel_reservation=hotel_reservation,
			adults=2,
			children=1,
			total_price=2250,
			status=TourReservation.Status.PENDING,
		)

		self.client.login(username='partner2@example.com', password='PartnerPass123!')
		response = self.client.get(reverse('partner-tour-sessions', kwargs={'tour_uuid': str(tour.uuid)}))

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertContains(response, '1 rezervasyon')
		self.assertContains(response, reverse('partner-session-reservations', kwargs={'tour_uuid': str(tour.uuid), 'session_id': session.id}))
		sessions = response.context['sessions']
		self.assertEqual(sessions[0].available_spots, 7)
		self.assertEqual(sessions[0].reservation_count, 1)

	def test_partner_sees_customer_cards_on_reservations_page(self):
		partner_user = User.objects.create_user(
			email='partner3@example.com',
			password='PartnerPass123!',
			full_name='Partner User 3',
			phone='+905551110002',
			country='TR',
			role=User.Role.PARTNER,
		)
		company = PartnerCompany.objects.create(
			user=partner_user,
			company_name='Card Partner Co',
			tax_number='TR998',
			is_approved=True,
		)
		destination = Destination.objects.create(name='Bodrum', active=True)
		tour = Tour.objects.create(
			provider=company,
			destination=destination,
			title='Sunset Cruise',
			description='Evening cruise',
			price_adult=1200,
			price_child=600,
			is_approved=True,
		)
		session = TourSession.objects.create(
			tour=tour,
			date=timezone.localdate() + timedelta(days=3),
			start_time='18:00',
			end_time='20:00',
			capacity=12,
			booked_count=4,
			is_active=True,
		)
		customer = User.objects.create_user(
			email='guest2@example.com',
			password='StrongPass123!',
			full_name='Card Guest',
			phone='+905551114444',
			country='TR',
		)
		hotel = Hotel.objects.create(
			name='Harbor Hotel',
			destination=destination,
			nightly_price_per_person=4100,
			currency='TRY',
			rating=4.9,
			family_friendly=True,
		)
		hotel_reservation = HotelReservation.objects.create(
			user=customer,
			hotel=hotel,
			start_date=timezone.localdate() + timedelta(days=2),
			end_date=timezone.localdate() + timedelta(days=5),
			adults=2,
			children=2,
			status=HotelReservation.Status.BOOKING_CONFIRMED,
		)
		TourReservation.objects.create(
			user=customer,
			session=session,
			hotel_reservation=hotel_reservation,
			adults=2,
			children=2,
			total_price=3600,
			status=TourReservation.Status.CONFIRMED,
		)

		self.client.login(username='partner3@example.com', password='PartnerPass123!')
		response = self.client.get(reverse('partner-session-reservations', kwargs={'tour_uuid': str(tour.uuid), 'session_id': session.id}))

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertContains(response, 'Card Guest')
		self.assertContains(response, 'guest2@example.com')
		self.assertContains(response, '+905551114444')
		self.assertContains(response, 'Harbor Hotel')
		self.assertContains(response, '4 kisi')
		self.assertEqual(len(response.context['reservations']), 1)
		self.assertEqual(response.context['reservations'][0]['hotel_name'], 'Harbor Hotel')

	def test_partner_can_update_session_availability(self):
		partner_user = User.objects.create_user(
			email='partner4@example.com',
			password='PartnerPass123!',
			full_name='Partner User 4',
			phone='+905551116666',
			country='TR',
			role=User.Role.PARTNER,
		)
		company = PartnerCompany.objects.create(
			user=partner_user,
			company_name='Availability Partner Co',
			tax_number='TR997',
			is_approved=True,
		)
		destination = Destination.objects.create(name='Fethiye', active=True)
		tour = Tour.objects.create(
			provider=company,
			destination=destination,
			title='Lagoon Boat',
			description='Daily boat tour',
			price_adult=950,
			price_child=475,
			is_approved=True,
		)
		session = TourSession.objects.create(
			tour=tour,
			date=timezone.localdate() + timedelta(days=4),
			start_time='11:00',
			end_time='13:00',
			capacity=20,
			booked_count=6,
			is_active=True,
		)

		self.client.login(username='partner4@example.com', password='PartnerPass123!')
		response = self.client.post(
			reverse('partner-tour-sessions', kwargs={'tour_uuid': str(tour.uuid)}),
			{
				'action': 'update',
				'session_id': session.id,
				f'session-{session.id}-capacity': 24,
				f'session-{session.id}-booked_count': 9,
				f'session-{session.id}-is_active': '',
			},
			follow=True,
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		session.refresh_from_db()
		self.assertEqual(session.capacity, 24)
		self.assertEqual(session.booked_count, 9)
		self.assertFalse(session.is_active)
		self.assertContains(response, 'Seans doluluk bilgisi guncellendi.')
		self.assertContains(response, '15')

	def test_partner_can_delete_empty_session(self):
		partner_user = User.objects.create_user(
			email='partner5@example.com',
			password='PartnerPass123!',
			full_name='Partner User 5',
			phone='+905551117777',
			country='TR',
			role=User.Role.PARTNER,
		)
		company = PartnerCompany.objects.create(
			user=partner_user,
			company_name='Delete Partner Co',
			tax_number='TR996',
			is_approved=True,
		)
		destination = Destination.objects.create(name='Kas', active=True)
		tour = Tour.objects.create(
			provider=company,
			destination=destination,
			title='Morning Swim',
			description='Empty session delete test',
			price_adult=700,
			price_child=350,
			is_approved=True,
		)
		session = TourSession.objects.create(
			tour=tour,
			date=timezone.localdate() + timedelta(days=6),
			start_time='08:00',
			end_time='10:00',
			capacity=10,
			booked_count=0,
			is_active=True,
		)

		self.client.login(username='partner5@example.com', password='PartnerPass123!')
		response = self.client.post(
			reverse('partner-tour-sessions', kwargs={'tour_uuid': str(tour.uuid)}),
			{
				'action': 'delete',
				'session_id': session.id,
			},
			follow=True,
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertFalse(TourSession.objects.filter(id=session.id).exists())
		self.assertContains(response, 'Seans silindi.')

	def test_partner_cannot_delete_session_with_reservations(self):
		partner_user = User.objects.create_user(
			email='partner6@example.com',
			password='PartnerPass123!',
			full_name='Partner User 6',
			phone='+905551118999',
			country='TR',
			role=User.Role.PARTNER,
		)
		company = PartnerCompany.objects.create(
			user=partner_user,
			company_name='Reserved Delete Co',
			tax_number='TR995',
			is_approved=True,
		)
		destination = Destination.objects.create(name='Alanya', active=True)
		tour = Tour.objects.create(
			provider=company,
			destination=destination,
			title='Reserved Session',
			description='Reservation guard test',
			price_adult=850,
			price_child=425,
			is_approved=True,
		)
		session = TourSession.objects.create(
			tour=tour,
			date=timezone.localdate() + timedelta(days=7),
			start_time='14:00',
			end_time='16:00',
			capacity=12,
			booked_count=2,
			is_active=True,
		)
		customer = User.objects.create_user(
			email='delete-guest@example.com',
			password='StrongPass123!',
			full_name='Delete Guest',
			phone='+905551119111',
			country='TR',
		)
		TourReservation.objects.create(
			user=customer,
			session=session,
			adults=2,
			children=0,
			total_price=1700,
			status=TourReservation.Status.PENDING,
		)

		self.client.login(username='partner6@example.com', password='PartnerPass123!')
		response = self.client.post(
			reverse('partner-tour-sessions', kwargs={'tour_uuid': str(tour.uuid)}),
			{
				'action': 'delete',
				'session_id': session.id,
			},
			follow=True,
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertTrue(TourSession.objects.filter(id=session.id).exists())
		self.assertContains(response, 'Rezervasyonu olan seans silinemez.')
