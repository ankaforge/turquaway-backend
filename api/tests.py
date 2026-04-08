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
