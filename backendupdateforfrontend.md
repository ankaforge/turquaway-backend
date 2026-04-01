# Backend Update To-Do

## Authentication Endpoints (Required for Mobile Auth Flow)

### POST `/api/auth/register/`
Request body:
```json
{
  "full_name": "string",
  "email": "user@example.com",
  "phone": "+905xxxxxxxxx",
  "country": "TR",
  "password": "string"
}
```
Response (201):
```json
{
  "access_token": "jwt_access_token",
  "refresh_token": "jwt_refresh_token"
}
```
- Validate unique email; return 400 with `detail` message on conflict.
- Password: min 8 chars, must not be entirely numeric.
- Country: accept 2-letter ISO 3166-1 alpha-2 codes only.

### POST `/api/auth/login/`
Request body:
```json
{
  "email": "user@example.com",
  "password": "string"
}
```
Response (200):
```json
{
  "access_token": "jwt_access_token",
  "refresh_token": "jwt_refresh_token"
}
```
- Return 401 with `detail` on invalid credentials (do NOT distinguish email vs password errors).

### POST `/api/auth/token/refresh/`
Request body:
```json
{ "refresh": "jwt_refresh_token" }
```
Response (200):
```json
{ "access": "new_jwt_access_token" }
```

### Token Strategy
- Use **djangorestframework-simplejwt** (or equivalent).
- Access token TTL: 30 minutes.
- Refresh token TTL: 30 days.
- All authenticated endpoints must accept `Authorization: Bearer <access_token>`.
- Mobile stores tokens in device SecureStore — never in AsyncStorage.
- Mobile stores tokens in device SecureStore — never in AsyncStorage.

---

## AI Planning Endpoints (Required for Core Flow)

### POST `/api/suggest-cities/`
Called from: `LoadingAIProcessingScreen`

Request body:
```json
{
  "budget_type": "luxury | economy | cheap",
  "activities": ["sea", "history", "food", "nature", "night", "photo"]
}
```
Response (200) — accepts any of these shapes (mobile normalizes):
```json
["Istanbul", "Antalya", "Kapadokya"]
```
veya:
```json
{
  "cities": [
    { "city": "Istanbul", "reason": "Tarihi doku ve gastronomi" },
    { "city": "Antalya", "reason": "Sahil ve aktivite zenginligi" }
  ]
}
```
veya:
```json
{
  "suggestions": [
    { "city": "Bodrum", "description": "Premıum sahıl deneyımi" }
  ]
}
```
- Dönen şehir sayısı: **3 (sabit)** — RouteSelectionScreen tam 3 rota kartı render eder.
- Her şehir için `city/name/title` alanlarından en az biri zorunlu.
- İsteğe bağlı: `reason` / `description` (alt başlık olarak gösterilir).
- Hatalarda `detail` alanıyla 4xx döndür; mobil `navigation.goBack()` yapar.

---

### POST `/api/generate-plan/`
Called from: `RouteSelectionScreen`

Request body:
```json
{
  "city": "Istanbul",
  "start_date": "2026-05-10",
  "end_date": "2026-05-13",
  "guests": 3,
  "adults": 2,
  "children": 1,
  "budget_type": "economy",
  "activities": ["history", "food"]
}
```
Response (200):
```json
{
  "itinerary_data": {
    "city": "Istanbul",
    "header_image": "https://...",
    "daily_plan": [
      {
        "day": 1,
        "title": "Tarihi Yarimada",
        "activities": [
          {
            "time": "09:00",
            "name": "Sultanahmet Meydani",
            "transportation_note": "Tramvay T1 ile ulasim kolay.",
            "price": null,
            "min_age": null,
            "family_friendly": true,
            "adult_only": false
          }
        ],
        "dining": [
          {
            "time": "19:30",
            "name": "Bogaz manzarali aksam yemegi",
            "price": "€65 ort.",
            "cuisine": "Turk mutfagi"
          }
        ]
      }
    ],
    "accommodation": [
      {
        "name": "The Bosphorus Palace",
        "area": "Besiktas",
        "price": "€240 / gece",
        "family_friendly": true,
        "child_bed_available": true,
        "adult_only": false
      }
    ]
  }
}
```

Alan eşlemeleri (mobil her iki notasyonu da kabul eder):
| Backend alanı | Alternatif alan | Kullanım yeri |
|---|---|---|
| `header_image` | `headerImage` | DailyItineraryScreen başlık görseli |
| `daily_plan` | `dailyPlans` | Günlük plan listesi |
| `accommodation` | `hotels` | Konaklama listesi |
| `activities[].name` | `activities[].title` | Aktivite başlığı |
| `activities[].transportation_note` | `activities[].transport` | Ulaşım notu |
| `dining[].name` | `dining[].restaurant` | Restoran adı |
| `dining[].price` | `dining[].average_price` | Fiyat bilgisi |

- `itinerary_data` wrapper zorunlu değil; backend direkt nesne de dönebilir (mobil her ikisini handle eder).
- `daily_plan` boş array dönerse mobil fallback plan gösterir — üretimde bu olmamalı.
- `header_image` null dönerse Unsplash fallback kullanılır.




## Critical Rule: Adult/Child Separation (Must Have)
- Make `adults` and `children` required request fields in itinerary generation payload.
- Keep `guests` as computed total (`adults + children`) only for compatibility, but do not use it as primary decision input.
- Reject requests if `adults` is missing or `< 1`.
- Reject requests if `children` is missing or `< 0`.
- Add strict validation: `guests === adults + children`.

## API and AI Flow
- Update itinerary endpoint contract to include: `language`, `adults`, `children`, `dates`, `budget`, `activity_preferences`.
- Store language + guest composition in request context before AI generation.
- Add retry and timeout strategy for AI itinerary generation requests.
- Return structured sections: `safe_for_children`, `age_notes`, `why_recommended`, `risk_flags` for each activity/hotel.

## Child Safety and Content Filtering (Gemini Responsibility)
- Define policy rules for child-unsafe items (nightlife, adult-only venues, unsafe transport windows, etc.).
- Force Gemini prompt to respect `children > 0` mode and avoid unsafe recommendations.
- Add post-generation rule checker on backend: remove or replace any unsafe activity/hotel before response.
- If unsafe suggestions are detected, regenerate only invalid sections with stricter prompt constraints.
- Add `family_mode: true` when `children > 0` and pass this as mandatory model instruction.

## Hotel and Activity Metadata Requirements
- Extend activity schema with `min_age`, `family_friendly`, `adult_only`, `safety_notes`.
- Extend hotel schema with `family_friendly`, `child_bed_available`, `adult_only`, `quiet_hours_info`.
- Prevent returning entries where `adult_only=true` when `children > 0`.
- Add fallback replacement strategy when filtered list becomes too short.

## User Profile and Preferences
- Create profile endpoint to read/write preferences: language, budget bias, activity priorities, child sensitivity level.
- Save latest `adults/children` preference as reusable profile defaults.
- Add secure update route for preference changes from mobile profile screen.

## Localization
- Add language parameter support for all itinerary and recommendation endpoints.
- Return language-ready text fields in selected language.
- Provide fallback language logic when requested language is unavailable.

## Reliability and Security
- Add input sanitization and request size limits.
- Add rate limiting for AI generation endpoints.
- Add structured error codes for mobile-friendly error handling.
- Add policy violation error type for child-safety filtering failures.

## Observability and QA
- Log request lifecycle with guest composition: received, validated, AI started, filtered, completed, failed.
- Add metrics: unsafe-item-detection-rate, filtered-item-count, family-mode-usage-rate.
- Add trace correlation id in all API responses for easier debugging.
- Build QA test cases:
- `children=0`: adult recommendations allowed.
- `children>0`: no adult-only activity/hotel must appear.
- Mixed language requests should still respect child-safety constraints.
