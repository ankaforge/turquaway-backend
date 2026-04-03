# TURQUAWAY BACKEND CONTRACT (ROADMAP ALIGNED)

Bu dokuman, sadece asagidaki kapsami hedefler:
- Adim 1: Karsilama + Dil + Auth
- Adim 2: Rezervasyon Hunisi
- Adim 3: Satin Alma ve Planlama

Amaç: Mobil uygulamanin bekledigi backend sozlesmesini netlestirmek.

## 0) Global Kurallar

### 0.1 Base URL ve Versiyonlama
- Base URL: /api/v1
- Tumu JSON doner.

### 0.2 Auth
- JWT: access_token + refresh_token
- Header: Authorization: Bearer <access_token>
- Access TTL: 30 dk
- Refresh TTL: 30 gun

### 0.3 Dil
- Desteklenen diller: tr, en, ru, ar
- Bilinmeyen dil geldiyse fallback: en
- Metin donen endpointlerde language/lang parametresi kabul edilmeli.

### 0.4 Standart Hata Formati
Tum hata response'lari bu formatta olmalidir:

```json
{
  "code": "validation_error",
  "detail": "Human readable message",
  "fields": {
    "email": ["Invalid email"]
  },
  "trace_id": "uuid"
}
```

### 0.5 Durum Kodlari
- 200: basarili okuma/aksiyon
- 201: olusturma
- 204: silme/icerik yok
- 400: validation
- 401: auth gerekli/gecersiz
- 403: yetki yok
- 404: bulunamadi
- 409: cakisma (or. email zaten var)
- 422: anlamsal hata
- 429: rate limit
- 500/502: sunucu veya upstream AI hatasi

---

## 1) ADIM 1 - Karsilama ve Kimlik Dogrulama

Not: Onboarding ve LanguageSelection frontend-first ekranlaridir. Backend tarafinda gerekli olanlar auth, profile ve legal consent kaydi.

### 1.1 Register
POST /api/v1/auth/register/

Request:
```json
{
  "full_name": "Ada Lovelace",
  "email": "ada@example.com",
  "phone": "+905551112233",
  "country": "TR",
  "password": "StrongPass123!",
  "password_confirm": "StrongPass123!",
  "language": "tr",
  "consents": {
    "terms_accepted": true,
    "privacy_accepted": true,
    "accepted_at": "2026-04-03T12:00:00Z",
    "version": "v1"
  }
}
```

Validation:
- full_name zorunlu
- email zorunlu + unique
- phone zorunlu
- country ISO alpha-2
- password min 8
- password == password_confirm
- terms_accepted ve privacy_accepted true olmali

Response 201:
```json
{
  "user": {
    "id": "uuid",
    "full_name": "Ada Lovelace",
    "email": "ada@example.com",
    "phone": "+905551112233",
    "country": "TR",
    "language": "tr"
  },
  "tokens": {
    "access_token": "jwt_access",
    "refresh_token": "jwt_refresh"
  }
}
```

### 1.2 Login
POST /api/v1/auth/login/

Request:
```json
{
  "email": "ada@example.com",
  "password": "StrongPass123!"
}
```

Response 200:
```json
{
  "user": {
    "id": "uuid",
    "full_name": "Ada Lovelace",
    "email": "ada@example.com",
    "language": "tr"
  },
  "tokens": {
    "access_token": "jwt_access",
    "refresh_token": "jwt_refresh"
  }
}
```

### 1.3 Refresh Token
POST /api/v1/auth/token/refresh/

Request:
```json
{
  "refresh_token": "jwt_refresh"
}
```

Response 200:
```json
{
  "access_token": "new_jwt_access"
}
```

### 1.4 Logout
POST /api/v1/auth/logout/

Request:
```json
{
  "refresh_token": "jwt_refresh"
}
```

Response 204

Not:
- Refresh blacklist veya rotation uygulanmali.

### 1.5 Me (Profile bootstrap)
GET /api/v1/me/

Response 200:
```json
{
  "id": "uuid",
  "full_name": "Ada Lovelace",
  "email": "ada@example.com",
  "phone": "+905551112233",
  "country": "TR",
  "language": "tr"
}
```

### 1.6 Dil Guncelleme
PATCH /api/v1/me/language/

Request:
```json
{
  "language": "ru"
}
```

Response 200:
```json
{
  "language": "ru"
}
```

---

## 2) ADIM 2 - Rezervasyon Hunisi

Huni state'i local draft olarak da tutuluyor; backend tarafi da server draft desteklemeli.

### 2.1 Draft Kaydet/Guncelle
PUT /api/v1/funnel/draft/

Request:
```json
{
  "start_date": "2026-05-10",
  "end_date": "2026-05-13",
  "adults": 2,
  "children": 1,
  "budget_type": "economy",
  "activities": ["safari", "diving"],
  "language": "tr"
}
```

Response 200:
```json
{
  "draft_id": "uuid",
  "updated_at": "2026-04-03T12:00:00Z"
}
```

### 2.2 Draft Oku
GET /api/v1/funnel/draft/

Response 200:
```json
{
  "start_date": "2026-05-10",
  "end_date": "2026-05-13",
  "adults": 2,
  "children": 1,
  "budget_type": "economy",
  "activities": ["safari", "diving"],
  "language": "tr"
}
```

### 2.3 Etkinlikleri Dinamik Cek
GET /api/v1/activities/?lang=tr

Response 200 (onerilen format):
```json
{
  "results": [
    {
      "key": "safari",
      "name": "Safari",
      "icon": "binoculars",
      "active": true
    },
    {
      "key": "diving",
      "name": "Dalis",
      "icon": "waves",
      "active": true
    }
  ]
}
```

Kurallar:
- key dil-bagimsiz sabit olmalidir.
- name secilen dile gore lokalize olmalidir.

### 2.4 AI Sehir Onerisi (LoadingAIProcessing)
POST /api/v1/ai/suggest-cities/

Request:
```json
{
  "start_date": "2026-05-10",
  "end_date": "2026-05-13",
  "adults": 2,
  "children": 1,
  "budget_type": "economy",
  "activities": ["safari", "diving"],
  "language": "tr",
  "family_mode": true
}
```

family_mode kurali:
- children > 0 ise family_mode zorunlu true
- children == 0 ise false olabilir

Response 200:
```json
{
  "cities": [
    {
      "city": "Antalya",
      "description": "Sahil ve aile aktiviteleri"
    },
    {
      "city": "Mugla",
      "description": "Dogal koylar ve sakin rota"
    },
    {
      "city": "Nevsehir",
      "description": "Kultur ve manzara odakli"
    }
  ]
}
```

Kurallar:
- Tam 3 rota donmeli.
- RouteSelection en ustte ilk 3 rotayi En Cok Tercih Edilenler etiketiyle gosterecek.

---

## 3) ADIM 3 - Satin Alma ve Planlama

Bu adim, yol haritasindaki ekranlarin backend sozlesmesidir.

### 3.1 HotelSelection - Otel Arama
POST /api/v1/hotels/search/

Request:
```json
{
  "city": "Antalya",
  "start_date": "2026-05-10",
  "end_date": "2026-05-13",
  "adults": 2,
  "children": 1,
  "budget_type": "economy",
  "activities": ["safari", "diving"],
  "language": "tr",
  "sort": "price_asc"
}
```

Response 200:
```json
{
  "hotels": [
    {
      "id": "uuid",
      "name": "Hotel A",
      "city": "Antalya",
      "nightly_price_per_person": 4200,
      "currency": "TRY",
      "rating": 4.5,
      "sponsored": true,
      "sponsored_badge": "Gemini Onerisi",
      "family_friendly": true,
      "distance_to_center_km": 1.8,
      "image": "https://..."
    }
  ]
}
```

Butce kurallari:
- cheap: nightly_price_per_person < 5000
- economy: nightly_price_per_person < 8000
- luxury: nightly_price_per_person > 12000

Sort parametreleri:
- price_asc
- price_desc
- value_score (AI fiyat/performans)

### 3.2 HotelReservation - Native Rezervasyon
POST /api/v1/hotel-reservations/

Request:
```json
{
  "hotel_id": "uuid",
  "start_date": "2026-05-10",
  "end_date": "2026-05-13",
  "adults": 2,
  "children": 1,
  "guest_contact": {
    "full_name": "Ada Lovelace",
    "email": "ada@example.com",
    "phone": "+905551112233"
  }
}
```

Response 201:
```json
{
  "reservation_id": "uuid",
  "status": "pending_payment",
  "payment": {
    "provider": "booking_demand_partner",
    "payment_intent_id": "pi_xxx",
    "client_secret": "secret_xxx"
  }
}
```

Webhook endpoint (partner -> backend):
- POST /api/v1/webhooks/hotel-reservations/

Beklenen olaylar:
- payment_succeeded
- payment_failed
- booking_confirmed
- booking_cancelled

### 3.3 TourSelection - Yakin Tur Listesi (30km)
POST /api/v1/tours/search/

Request:
```json
{
  "hotel_id": "uuid",
  "city": "Antalya",
  "adults": 2,
  "children": 1,
  "budget_type": "economy",
  "activities": ["safari", "diving"],
  "radius_km": 30,
  "language": "tr"
}
```

Response 200:
```json
{
  "tours": [
    {
      "id": "uuid",
      "title": "Kanyon Safari",
      "description": "Tam gun doga turu",
      "price_adult": 1800,
      "price_child": 900,
      "currency": "TRY",
      "distance_km": 12.4,
      "family_friendly": true,
      "categories": ["safari"],
      "provider": {
        "id": "uuid",
        "name": "Partner Tour A"
      }
    }
  ],
  "empty_state": false,
  "diy_fallback": null
}
```

Bos durum:
- Eger tour yoksa hata donme.
- 200 + empty_state true don.
- Backend arka planda DIY fallback plan uretebilir.

Bos response ornegi:
```json
{
  "tours": [],
  "empty_state": true,
  "diy_fallback": {
    "title": "Kendin Yap Rota",
    "summary": "Bolgede anlasmali tur yok, sana ozel serbest gezi plani olusturuldu."
  }
}
```

### 3.4 PlanSelection - 2 Plan Uret
POST /api/v1/plans/generate-options/

Request:
```json
{
  "city": "Antalya",
  "start_date": "2026-05-10",
  "end_date": "2026-05-13",
  "adults": 2,
  "children": 1,
  "budget_type": "economy",
  "activities": ["safari", "diving"],
  "hotel_reservation_id": "uuid",
  "selected_tour_ids": ["uuid"],
  "language": "tr",
  "family_mode": true
}
```

Response 200:
```json
{
  "options": [
    {
      "plan_id": "uuid_plan_1",
      "title": "Plan A",
      "days": [
        {
          "day": 1,
          "timeline": [
            {
              "time": "09:00",
              "type": "activity",
              "title": "Liman Gezisi",
              "notes": "Aileye uygun"
            }
          ]
        }
      ],
      "estimated_total": 12400,
      "currency": "TRY"
    },
    {
      "plan_id": "uuid_plan_2",
      "title": "Plan B",
      "days": [],
      "estimated_total": 13800,
      "currency": "TRY"
    }
  ]
}
```

Kurallar:
- Tam 2 plan donmeli.
- Timeline saat saat formatta olmalidir.

### 3.5 Plan Secimi Onayla
POST /api/v1/plans/confirm/

Request:
```json
{
  "plan_id": "uuid_plan_1"
}
```

Response 200:
```json
{
  "status": "confirmed",
  "confirmed_plan_id": "uuid_plan_1",
  "tour_reservations_created": 2
}
```

### 3.6 PlanScreen - Aktif Plani Getir
GET /api/v1/plans/current/

Response 200:
```json
{
  "plan_id": "uuid_plan_1",
  "city": "Antalya",
  "status": "active",
  "days": [
    {
      "day": 1,
      "timeline": []
    }
  ]
}
```

### 3.7 Huniyi Bastan Baslat
POST /api/v1/plans/restart/

Response 204

Etkisi:
- aktif draft temizlenir
- aktif secim temizlenir
- kullanici yeniden DateRangeGuests adimina donebilir

---

## 4) Django Tarafi - Model Taslagi (MVP)

Asagidaki modeller adim 1-2-3 kontratini desteklemek icin yeterlidir.

1. UserProfile
- user (OneToOne)
- full_name
- phone
- country
- language

2. UserLegalConsent
- user (FK)
- terms_accepted
- privacy_accepted
- accepted_at
- version

3. FunnelDraft
- user (OneToOne)
- start_date
- end_date
- adults
- children
- budget_type
- activities (JSON)
- selected_city
- updated_at

4. ActivityCategory
- key (unique)
- name_tr
- name_en
- name_ru
- name_ar
- icon
- active

5. Hotel
- external_hotel_id
- name
- city
- nightly_price_per_person
- currency
- rating
- sponsored
- family_friendly
- image

6. HotelReservation
- user
- hotel
- start_date
- end_date
- adults
- children
- status
- payment_provider
- payment_intent_id

7. Tour
- provider
- title
- description
- city
- lat
- lng
- price_adult
- price_child
- family_friendly
- categories (M2M ActivityCategory)

8. TourReservation
- user
- tour
- hotel_reservation
- date
- adults
- children
- status

9. TravelPlan
- user
- source_payload (JSON)
- options_payload (JSON)
- confirmed_plan_id
- status (draft/confirmed/active/completed)

---

## 5) Django URL Taslagi

ornek api/urls.py:

```python
from django.urls import path
from . import views

urlpatterns = [
    path("auth/register/", views.RegisterView.as_view()),
    path("auth/login/", views.LoginView.as_view()),
    path("auth/token/refresh/", views.RefreshTokenView.as_view()),
    path("auth/logout/", views.LogoutView.as_view()),

    path("me/", views.MeView.as_view()),
    path("me/language/", views.MeLanguageView.as_view()),

    path("funnel/draft/", views.FunnelDraftView.as_view()),
    path("activities/", views.ActivityListView.as_view()),

    path("ai/suggest-cities/", views.SuggestCitiesView.as_view()),

    path("hotels/search/", views.HotelSearchView.as_view()),
    path("hotel-reservations/", views.HotelReservationCreateView.as_view()),
    path("webhooks/hotel-reservations/", views.HotelReservationWebhookView.as_view()),

    path("tours/search/", views.TourSearchView.as_view()),

    path("plans/generate-options/", views.PlanGenerateOptionsView.as_view()),
    path("plans/confirm/", views.PlanConfirmView.as_view()),
    path("plans/current/", views.PlanCurrentView.as_view()),
    path("plans/restart/", views.PlanRestartView.as_view()),
]
```

---

## 6) Frontend-Backend Uyum Notlari (Kritik)

- adults backend tarafinda zorunludur.
- children backend tarafinda zorunludur (0 olabilir).
- family_mode, children > 0 ise true olarak ele alinmalidir.
- Dil secimi tum AI metinlerinde dikkate alinmalidir.
- Etkinlik endpointi her zaman stabil key donmelidir.
- Suggest-cities her zaman 3 destinasyon donmelidir.
- PlanSelection her zaman 2 plan secenegi donmelidir.

Bu kurallar, mevcut mobil akisin sorunsuz calismasi icin zorunludur.
