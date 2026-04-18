from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from api.models import (
	Destination,
	Hotel,
	HotelReservation,
	PartnerCompany,
	Tour,
	TourReservation,
	TourSession,
	User,
)


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
