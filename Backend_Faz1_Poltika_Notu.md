# TURQUAWAY Backend Ekibi Icin Faz-1 Politika Notu

Tarih: 2026-06-14

Bu metin, mobil uygulamada aktif olan Faz-1 davranisini backend tarafinda net ve stabil sekilde desteklemek icin hazirlanmistir. Buradaki maddeler Faz-1 canli kosullarda baglayicidir.

## 1) Faz-1 Kapsami (Net Sinir)

Faz-1'de hedef, sadece AI destekli plan olusturma akisidir.

- Otel rezervasyonu aktif degildir.
- Tur rezervasyonu aktif degildir.
- Legacy akislardaki DateRangeGuests, LoadingAIProcessing, RouteSelection, HotelSelection, HotelReservation, TourSelection ekranlari devre disidir.
- Uygulamada aktif funnel: StayDetails -> BudgetSelection -> IventSelection -> PlanSelection -> Plan

Bu nedenle backend Faz-1'de sadece mevcut funnel'i besleyen endpointleri kritik kabul etmelidir.

## 2) Faz-1'de Zorunlu Endpoint Seti

Asagidaki endpointler Faz-1 icin minimum calisir paket olarak ele alinmalidir:

- Auth:
  - POST /api/v1/auth/register/
  - POST /api/v1/auth/login/
  - POST /api/v1/auth/token/refresh/
  - POST /api/v1/auth/logout/
- Profil:
  - GET /api/v1/me/
  - PATCH /api/v1/me/language/
  - PATCH /api/v1/me/ (hesap bilgisi guncelleme)
  - POST /api/v1/me/password/ (sifre degistirme)
- Planlama (Faz-1 aktif akis):
  - POST /api/v1/plans/generate-options/
  - POST /api/v1/plans/confirm/
  - GET /api/v1/plans/current/
  - GET /api/v1/plans/
  - POST /api/v1/plans/restart/
- Destekleyici:
  - GET /api/v1/activities/
  - GET /api/v1/config/mobile/ (feature flag/remote config)

Not: GET /api/v1/me/reservations/ ve voucher endpointleri uygulamada yer alsa da Faz-1 is hedefinin merkezinde degildir; stabilite riski olusturmadan bos liste donebilir.

## 3) Faz-1 Is Kurallari

### 3.1 Plan Secenekleri

- plans/generate-options her zaman 2 adet plan secenegi donmelidir.
- Her plan seceneginde days/timeline yapisi bulunmalidir (bos olabilir ama tip tutarliligi korunmalidir).
- language parametresi AI metinlerinde dikkate alinmalidir.

### 3.2 Plan Onayi ve Aktif Plan

- plans/confirm secilen plani kullaniciya baglamalidir.
- plans/current her zaman kullanicinin aktif planini dondurmeyi denemelidir.
- plans/current gecici olarak bos donerse mobil fallback ile devam eder; fakat bu durum operasyonel hata olarak izlenmelidir.

### 3.3 Coklu Plan Destegi

- plans/ endpointi kullanicinin tum planlarini listelemelidir.
- Mobil taraf planlari ongoing/upcoming/past olarak tarih alanlarina gore siniflar.
- Bu nedenle start_date ve end_date alanlari zorunlu ve dogru formatta donmelidir.

### 3.4 Restart Davranisi

- plans/restart kullanicinin aktif planlama context'ini temizlemelidir.
- Basarili durumda 204 donulmesi beklenir.

## 4) Veri Sozlesmesi ve Hata Sozlesmesi

Tum Faz-1 endpointlerinde asagidaki prensip korunmalidir:

- Base API: /api/v1
- JWT access + refresh
- Standart hata formati:
  - code
  - detail
  - fields
  - trace_id
- HTTP kod tutarliligi:
  - 200/201/204 basarili
  - 400 validation
  - 401 auth
  - 403 yetki
  - 404 bulunamadi
  - 409 cakisma
  - 422 anlamsal hata
  - 429 rate limit
  - 5xx sunucu/upstream

## 5) Feature Flag Politikasi (Faz-1)

Faz geri alma ve kontrollu rollout icin backend tarafi su alanlari config endpointinden servis etmelidir:

- phase_mode: phase1
- ai_entry_mode: hotel_or_region veya mevcut funnel'a denk gelen aktif mod
- hotel_booking_enabled: false
- tour_booking_enabled: false
- ads_interstitial_on_ai_generate: operasyon kararina gore
- ads_banner_on_plan_screen: operasyon kararina gore

Zorunlu ilke: Faz-1 boyunca hotel_booking_enabled ve tour_booking_enabled false kalmalidir.

## 6) Dayaniklilik ve Fallback Politikasi

- AI uretiminde timeout/retry/backoff uygulanmalidir.
- plans/generate-options endpointi reservation bagimliligi yuzunden 4xx veriyorsa Faz-1 akis kirilir; bu durum engellenmelidir.
- tours/search endpointinin hotel_id zorunlulugu Faz-1 akisinda bloklayici olmamalidir (Faz-1'de tur akisi devre disi).

## 7) Gozlemlenebilirlik ve Operasyon

Faz-1 canli izleme icin minimum telemetri:

- request_id/trace_id
- user_id (varsa)
- endpoint bazli latency p50/p95
- AI plan endpoint hata orani
- timeout orani

Alarm onerisi:

- plans/generate-options 5xx > %5
- plans/current hata orani > %3
- auth/login hata orani > %3

## 8) Backend Ekibinden Beklenen Net Cikti

1. Faz-1 icin yukaridaki endpoint setinin stabil hale getirilmesi
2. plans/generate-options ve plans/current icin tutarli response sozlesmesi
3. plans/ liste endpointinin tarih alanlariyla tam uyumlu hale getirilmesi
4. feature flaglerin Faz-1 kilitleriyle (hotel/tour false) canliya alinmasi
5. standart hata formati ve trace_id zorunlulugunun tum endpointlere uygulanmasi

Bu not, Faz-1 suresince backend degisikliklerinde referans karar metni olarak kullanilmalidir.