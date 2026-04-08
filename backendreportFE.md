# Turquaway Backend — Frontend Entegrasyon Raporu

> Hazırlanma tarihi: 3 Nisan 2026  
> Kapsam: Adım 1 (Auth & Profil) · Adım 2 (Rezervasyon Hunisi) · Adım 3 (Satın Alma & Planlama)

## Mobil App Akışı

Mobil uygulama tarafında beklenen akış aşağıdaki gibidir:

1. Kullanıcı tarih aralığını seçer.
2. Kullanıcı kişi sayısını ve bütçe tipini seçer.
3. Kullanıcı aktivite tercihlerini seçer.
4. Gemini destekli destinasyon önerisi alınır ve kullanıcı şehir seçer.
5. Şehir bazlı oteller listelenir, kullanıcı otel seçer.
6. Otel rezervasyonu oluşturulur.
7. Kullanıcı isterse tur seçer, isterse tur seçmeden devam eder.
8. Seçili otel rezervasyonu ve seçili turlar ile Gemini iki plan önerisi üretir.
9. Kullanıcı planlardan birini onaylar.
10. Onay anında seçilmiş turlar için otomatik tur rezervasyonu oluşturulur.
11. Kullanıcı aktif planını takip ekranından izler.

Önemli notlar:
- Tur seçimi opsiyoneldir.
- Plan üretiminde her zaman 2 seçenek döner.
- Plan onayı, tur rezervasyonlarının gerçekten oluştuğu adımdır.
- Seçili tur yoksa plan aktif olabilir, ancak tur rezervasyonu oluşturulmaz.

---

## 0. Genel Kurallar

| Kural | Değer |
|---|---|
| Base URL | `/api/v1` |
| Format | JSON |
| Auth header | `Authorization: Bearer <access_token>` |
| Access token TTL | 30 dakika |
| Refresh token TTL | 30 gün |
| Refresh politikası | Rotation + Blacklist (her refresh'te yeni token) |
| Desteklenen diller | `tr` · `en` · `ru` · `ar` |
| Bilinmeyen dil | Fallback → `en` |

### Standart Hata Formatı

Tüm hata yanıtları aşağıdaki yapıda döner:

```json
{
  "code": "validation_error",
  "detail": "İnsan tarafından okunabilir mesaj",
  "fields": {
    "email": ["Bu alan zorunludur."]
  },
  "trace_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

| HTTP Kodu | Anlamı |
|---|---|
| 200 | Başarılı okuma / aksiyon |
| 201 | Oluşturma başarılı |
| 204 | Silme / boş içerik |
| 400 | Validation hatası |
| 401 | Auth gerekli veya geçersiz token |
| 403 | Yetersiz yetki |
| 404 | Kayıt bulunamadı |
| 409 | Çakışma (örn. email zaten kayıtlı) |
| 502 | Upstream AI hatası |

---

## 1. Auth & Profil Endpointleri

### 1.1 Kayıt Ol

```
POST /api/v1/auth/register/
```

**Request:**
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

**Response 201:**
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
    "access_token": "...",
    "refresh_token": "..."
  }
}
```

**Validasyon kuralları:**
- `full_name`, `email`, `phone`, `country`, `password`, `password_confirm` zorunlu
- `email` unique olmalı → çakışmada `409`
- `country` ISO 3166-1 alpha-2 (2 harf)
- Şifre min 8 karakter, tamamı sayısal olamaz
- `password == password_confirm`
- `terms_accepted` ve `privacy_accepted` → `true` zorunlu
- `consents.accepted_at` → geçerli ISO 8601 datetime

---

### 1.2 Giriş Yap

```
POST /api/v1/auth/login/
```

**Request:**
```json
{
  "email": "ada@example.com",
  "password": "StrongPass123!"
}
```

**Response 200:**
```json
{
  "user": {
    "id": "uuid",
    "full_name": "Ada Lovelace",
    "email": "ada@example.com",
    "language": "tr"
  },
  "tokens": {
    "access_token": "...",
    "refresh_token": "..."
  }
}
```

---

### 1.3 Token Yenile

```
POST /api/v1/auth/token/refresh/
```

**Request:**
```json
{
  "refresh_token": "..."
}
```

**Response 200:**
```json
{
  "access_token": "..."
}
```

> ⚠️ **Blacklist + Rotation politikası:** `refresh_token` tek kullanımlıktır. Bir kez `/auth/token/refresh/` çağrıldığında o token veritabanındaki kara listeye eklenir ve bir daha kullanılamaz. Bu endpoint yalnızca yeni `access_token` döner; yeni bir `refresh_token` üretmez. Refresh token'ı kaybetmeden saklamanız ve yalnızca access token süresi dolduğunda kullanmanız gerekir. Token çalınsa bile tekrar kullanılamaz.

---

### 1.4 Çıkış Yap

```
POST /api/v1/auth/logout/
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "refresh_token": "..."
}
```

**Response:** `204 No Content`

---

### 1.5 Profil Bilgisi

```
GET /api/v1/me/
Authorization: Bearer <access_token>
```

**Response 200:**
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

---

### 1.6 Dil Güncelle

```
PATCH /api/v1/me/language/
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "language": "ru"
}
```

**Response 200:**
```json
{
  "language": "ru"
}
```

> Geçerli değerler: `tr` · `en` · `ru` · `ar`

---

## 2. Rezervasyon Hunisi

### 2.1 Draft Kaydet / Güncelle

```
PUT /api/v1/funnel/draft/
Authorization: Bearer <access_token>
```

**Request:**
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

**Response 200:**
```json
{
  "draft_id": "uuid",
  "updated_at": "2026-04-03T12:00:00Z"
}
```

> Kullanıcı başına tek draft tutulur. Tekrar `PUT` yapılırsa mevcut draft güncellenir.

---

### 2.2 Draft Oku

```
GET /api/v1/funnel/draft/
Authorization: Bearer <access_token>
```

**Response 200:**
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

> Draft yoksa boş varsayılanlar döner (`adults: 1`, `children: 0` vb.).

---

### 2.3 Aktiviteleri Listele

```
GET /api/v1/activities/?lang=tr
```

**Auth:** Gerekmez (public)

**Response 200:**
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
      "name": "Dalış",
      "icon": "waves",
      "active": true
    }
  ]
}
```

> `key` dil bağımsız sabittir. `name` seçili dile göre lokalize döner.  
> Query param: `lang` veya `language` kabul edilir.

---

### 2.4 AI Şehir Önerisi

```
POST /api/v1/ai/suggest-cities/
Authorization: Bearer <access_token>
```

**Request:**
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

**Response 200:**
```json
{
  "cities": [
    { "city": "Antalya", "description": "Sahil ve aile aktiviteleri" },
    { "city": "Muğla", "description": "Doğal koylar ve sakin rota" },
    { "city": "Nevşehir", "description": "Kültür ve manzara odaklı" }
  ]
}
```

> **Her zaman tam 3 şehir döner.** Gemini başarısız olursa güvenli fallback aktif edilir.  
> `children > 0` ise `family_mode: true` zorunludur.

---

## 3. Satın Alma & Planlama

### 3.1 Otel Arama

```
POST /api/v1/hotels/search/
Authorization: Bearer <access_token>
```

**Request:**
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

**Response 200:**
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

**Bütçe filtreleri:**

| `budget_type` | Fiyat aralığı |
|---|---|
| `cheap` | < 5.000 TRY/gece |
| `economy` | < 8.000 TRY/gece |
| `luxury` | > 12.000 TRY/gece |

**`sort` seçenekleri:** `price_asc` · `price_desc` · `value_score`

---

### 3.2 Otel Rezervasyonu

```
POST /api/v1/hotel-reservations/
Authorization: Bearer <access_token>
```

**Request:**
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

**Response 201:**
```json
{
  "reservation_id": "uuid",
  "status": "pending_payment",
  "payment": {
    "provider": "booking_demand_partner",
    "payment_intent_id": "pi_xxxxx",
    "client_secret": "secret_xxxxx"
  }
}
```

**Rezervasyon durum akışı:**

```
pending_payment → payment_succeeded → booking_confirmed
               → payment_failed
               → booking_cancelled
```

**Webhook (partner → backend):**
```
POST /api/v1/webhooks/hotel-reservations/

{
  "event": "payment_succeeded",
  "payment_intent_id": "pi_xxxxx"
}
```

---

### 3.3 Tur Arama

```
POST /api/v1/tours/search/
Authorization: Bearer <access_token>
```

**Request:**
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

**Response 200 — Turlar varsa:**
```json
{
  "tours": [
    {
      "id": "uuid",
      "title": "Kanyon Safari",
      "description": "Tam gün doğa turu",
      "price_adult": 1800,
      "price_child": 900,
      "currency": "TRY",
      "distance_km": 12.4,
      "family_friendly": true,
      "categories": ["safari"],
      "location_link": "https://maps.google.com/...",
      "services": {
        "free_food_drinks": true,
        "hotel_pickup_dropoff": true
      },
      "provider": {
        "id": "uuid",
        "name": "Partner Tour A"
      },
      "available_sessions": [
        {
          "session_id": 14,
          "date": "2026-05-11",
          "start_time": "09:00:00",
          "end_time": "17:00:00",
          "capacity": 20,
          "available_spots": 13,
          "is_active": true
        }
      ]
    }
  ],
  "empty_state": false,
  "diy_fallback": null
}
```

Mobil app tarafı bu adımda:
- Tur seçimini `id` ile tutmalı.
- Kullanıcıya uygun seansları `available_sessions` içinden göstermeli.
- UI mantığını `session_id` bazlı kurmalı.
- Kullanıcı tur seçmezse `selected_tour_ids: []` ile devam edebilir.

**Response 200 — Tur yoksa:**
```json
{
  "tours": [],
  "empty_state": true,
  "diy_fallback": {
    "title": "Kendin Yap Rota",
    "summary": "Bölgede anlaşmalı tur yok, sana özel serbest gezi planı oluşturuldu."
  }
}
```

> Boş durumda 404 **dönmez**. `empty_state: true` + `diy_fallback` döner.

---

### 3.4 Plan Seçenekleri Üret

```
POST /api/v1/plans/generate-options/
Authorization: Bearer <access_token>
```

**Request:**
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

Frontend anlamı:
- `hotel_reservation_id`: bu akışta biraz önce oluşturulmuş otel rezervasyonu
- `selected_tour_ids`: kullanıcının seçtiği tur UUID listesi
- `selected_tour_ids` boş olabilir

**Response 200:**
```json
{
  "options": [
    {
      "plan_id": "plan_1_xxxxxxxxxx",
      "title": "Plan A",
      "days": [
        {
          "day": 1,
          "timeline": [
            {
              "time": "09:00",
              "type": "activity",
              "title": "Kanyon Safari",
              "notes": "Önceden seçilen tur. Otelden transfer ve öğle yemeği dahil."
            },
            {
              "time": "18:30",
              "type": "meal",
              "title": "Liman çevresinde akşam yemeği",
              "notes": "Tur saatine çakışmayacak şekilde planlandı."
            }
          ]
        }
      ],
      "estimated_total": 12400,
      "currency": "TRY"
    },
    {
      "plan_id": "plan_2_xxxxxxxxxx",
      "title": "Plan B",
      "days": [...],
      "estimated_total": 13800,
      "currency": "TRY"
    }
  ]
}
```

Gemini bu aşamada şu bağlamı kullanır:
- şehir
- tarih aralığı
- bütçe tipi
- aktiviteler
- dil
- aile modu
- otel adı
- seçilen turların başlıkları
- seçilen turların uygun tarih ve saat bilgileri
- seçilen turların servis bilgileri

> **Her zaman tam 2 seçenek döner.** `plan_id` değerlerini saklayın, bir sonraki adımda kullanılır.

---

### 3.5 Plan Onayla

```
POST /api/v1/plans/confirm/
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "plan_id": "plan_1_xxxxxxxxxx"
}
```

**Response 200:**
```json
{
  "status": "confirmed",
  "confirmed_plan_id": "plan_1_xxxxxxxxxx",
  "tour_reservations_created": 2
}
```

Bu endpoint çağrıldığında backend:
- seçili planı aktif hale getirir
- `selected_tour_ids` listesindeki turlar için tatil tarih aralığına uygun ilk aktif seansı bulur
- kapasite uygunsa tur rezervasyonlarını oluşturur
- seans doluluk bilgisini artırır

Mobil app beklentisi:
- Kullanıcı plan seçmeden bu endpoint çağrılmamalı.
- `tour_reservations_created` değeri kontrol edilmeli.
- Bu adımdan sonra kullanıcı `plans/current/` veya `me/reservations/?type=tour` ekranına yönlendirilebilir.

---

### 3.6 Aktif Planı Getir

```
GET /api/v1/plans/current/
Authorization: Bearer <access_token>
```

**Response 200:**
```json
{
  "plan_id": "plan_1_xxxxxxxxxx",
  "city": "Antalya",
  "status": "active",
  "days": [
    {
      "day": 1,
      "timeline": [...]
    }
  ]
}
```

> Aktif plan yoksa `404` döner.

Bu endpoint mobil uygulamadaki plan takip ekranı için kullanılmalıdır.

---

### 3.6.1 Opsiyonel Doğrudan Tur Rezervasyonu

Ana akış plan onayı ile otomatik rezervasyondur. Yine de tek bir seansı doğrudan rezerve etmek için aşağıdaki endpoint kullanılabilir:

```
POST /api/v1/tour-reservations/
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "session_id": 14,
  "adults": 2,
  "children": 1,
  "hotel_reservation_id": "uuid"
}
```

**Response 201:**
```json
{
  "reservation_id": "uuid",
  "status": "pending",
  "tour": {
    "id": "uuid",
    "title": "Kanyon Safari"
  },
  "session": {
    "session_id": 14,
    "date": "2026-05-11",
    "start_time": "09:00:00",
    "end_time": "17:00:00"
  },
  "adults": 2,
  "children": 1,
  "total_price": 4500,
  "currency": "TRY"
}
```

Bu endpoint mobil ana akış için zorunlu değildir.

---

### 3.7 Huniyi Sıfırla

```
POST /api/v1/plans/restart/
Authorization: Bearer <access_token>
```

**Response:** `204 No Content`

**Etkileri:**
- Kullanıcının aktif draft'ı silinir
- Aktif/draft planlar `completed` olarak işaretlenir
- Kullanıcı baştan tarih seçimi adımına dönebilir

---

## 4. Kritik Frontend Kuralları

| Kural | Detay |
|---|---|
| `adults` | Backend'de her zaman zorunlu, min `1` |
| `children` | Backend'de zorunlu, `0` olabilir |
| `family_mode` | `children > 0` ise mutlaka `true` gönderilmeli |
| `language` | AI metin üretimi dahil tüm endpointlerde dikkate alınır |
| Aktivite `key` | Dil bağımsız sabittir. Hiçbir zaman `name` gönderme |
| Şehir önerisi | Daima 3 sonuç döner |
| Plan seçenekleri | Daima 2 seçenek döner; `plan_id` kaybolmamalı |
| Tur seçimi | `selected_tour_ids` boş gönderilebilir |
| Tur kartı | `available_sessions` ve `services` alanları dikkate alınmalı |
| Tour boş durum | `404` değil `empty_state: true` bekle |
| Plan onayı | Seçili turlar varsa bu adım rezervasyon da oluşturur |
| Token yenileme | Eski `refresh_token` tek kullanımlık; yeni token'ı sakla |
| Tüm hatalar | `code` + `detail` + `fields` + `trace_id` formatında |

---

## 5. API Dokümantasyonu

| URL | Açıklama |
|---|---|
| `/api/docs/` | Swagger UI (interaktif) |
| `/api/redoc/` | ReDoc |
| `/api/schema/` | OpenAPI 3 JSON/YAML şeması |

---

## 6. Ortam & Yapılandırma Notları

- **GEMINI_API_KEY** env değişkeni yoksa `SuggestCitiesView` sabit fallback döner; gerçek AI önerisi gelmez.
- **CORS:** Geliştirme ortamında `localhost:19006`, `localhost:8081`, `localhost:3000` açıktır.
- **Veritabanı:** Geliştirmede SQLite; production için Postgres önerilir.
- **Statik dosyalar:** `STATIC_URL = /static/`; production'da `collectstatic` çalıştırılmalı.
