# RoadTracer

## Adım 1

Bu adımda proje için temel backend altyapısı, ortam değişkenleri, CORS ayarları ve API dokümantasyon sistemi kuruldu.

### Yapılanlar

- `requirements.txt` incelendi ve mevcut bağımlılıklar doğrulandı.
- `main/settings.py` dosyasında `INSTALLED_APPS` alanı güncellendi.
- `django-cors-headers`, `djangorestframework`, `drf-spectacular` ve `api` uygulaması projeye tanımlandı.
- `MIDDLEWARE` içine `corsheaders.middleware.CorsMiddleware` eklendi.
- `.env` desteği için `django-environ` kuruldu ve ayarlar bu yapı ile okunacak şekilde düzenlendi.
- `DJANGO_SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS` ve `GEMINI_API_KEY` için ortam değişkeni altyapısı eklendi.
- React Native Expo geliştirme süreci için uygun CORS ayarları tanımlandı.
- `.env` dosyası oluşturuldu.
- `.gitignore` dosyası oluşturularak `.env`, `env/`, `__pycache__/`, `*.pyc` ve `db.sqlite3` ignore listesine eklendi.

### Dokümantasyon Kurulumu

- OpenAPI/Swagger dokümantasyonu için `drf-spectacular` kuruldu.
- `REST_FRAMEWORK` içinde varsayılan schema sınıfı `drf_spectacular.openapi.AutoSchema` olarak ayarlandı.
- `SPECTACULAR_SETTINGS` ile API başlığı, açıklaması ve versiyonu tanımlandı.
- Aşağıdaki uçlar projeye eklendi:
  - `/api/schema/`
  - `/api/docs/`
  - `/api/redoc/`

### API Başlangıç Yapısı

- `api/urls.py` dosyası oluşturuldu.
- `api/views.py` içine örnek bir health check endpoint eklendi.
- `/api/health/` endpoint'i tanımlandı.
- Swagger üzerinde örnek görünmesi için bu endpoint schema ile etiketlendi.

### Doğrulama

- Kurulan yeni paketler `requirements.txt` dosyasına işlendi.
- `python manage.py check` çalıştırıldı.
- Sonuç: Django sistem kontrolü hatasız geçti.

### Not

- Ortamda `urllib3` ve `LibreSSL` ile ilgili bir uyarı görüldü; bu, uygulanan Django yapılandırmasının çalışmasını engelleyen bir hata değil.

## Adım 2

Bu adımda seyahat planı verisini saklamak için model ve serializer katmanı oluşturuldu.

### Yapılanlar

- `api/models.py` dosyasına `TravelPlan` modeli eklendi.
- Model alanları:
  - `user` (opsiyonel `ForeignKey`, `AUTH_USER_MODEL`)
  - `budget_type` (`Luxury`, `Economy`, `Cheap` seçenekli)
  - `activities` (`JSONField`)
  - `city` (`CharField`)
  - `start_date` (`DateField`)
  - `end_date` (`DateField`)
  - `guests` (`PositiveIntegerField`)
  - `itinerary_data` (Gemini çıktısını saklamak için `JSONField`)
- `api/serializers.py` dosyası oluşturuldu.
- Eklenen serializer'lar:
  - `TravelPlanSerializer` (tüm alanlar ve tarih sıralaması doğrulaması)
  - `TravelPlanSummarySerializer` (listeleme/özet kullanımına uygun sade çıktı)

### Doğrulama

- `python manage.py makemigrations api` çalıştırıldı.
- `api/migrations/0001_initial.py` oluşturuldu.
- `python manage.py check` çalıştırıldı ve sistem kontrolü hatasız geçti.

## Adım 3

Bu adımda Gemini entegrasyonu için servis katmanı eklendi.

### Yapılanlar

- `api/utils.py` dosyası oluşturuldu.
- `GeminiService` sınıfı yazıldı.
- `google-generativeai` ile model konfigürasyonu eklendi.
- `response_mime_type` değeri `application/json` olarak zorlandı.
- `get_city_suggestions(budget, activities)` metodu eklendi:
  - Bütçe + aktivite bazlı 3-5 şehir önerisi için prompt gönderiyor.
  - Dönen sonucu temizleyip JSON listesi olarak parse ediyor.
  - Liste uzunluğunu 3-5 aralığında doğruluyor.
- `create_detailed_plan(city, dates, guests, budget, activities)` metodu eklendi:
  - Günlük plan, otel, yemek, ulaşım ve maliyet kırılımı içeren kapsamlı plan üretiyor.
  - Sonucu JSON object olarak parse edip döndürüyor.
- Parse güvenliği için yardımcı metotlar eklendi:
  - Kod bloğu/fence temizliği
  - JSON parse ve tip doğrulaması

## Adım 4

Bu adımda Gemini servislerini kullanan API endpointleri eklendi ve URL bağlantıları tamamlandı.

### Yapılanlar

- `api/views.py` dosyasına iki yeni `APIView` eklendi:
  - `SuggestCitiesView`
  - `GeneratePlanView`
- `SuggestCitiesView` (POST):
  - `budget` ve `activities` verilerini alır.
  - `GeminiService.get_city_suggestions(...)` metodunu çağırır.
  - 3-5 şehir önerisini JSON response olarak döner.
- `GeneratePlanView` (POST):
  - `city`, `start_date`, `end_date`, `guests`, `budget`, `activities` verilerini alır.
  - `GeminiService.create_detailed_plan(...)` metodunu çağırır.
  - Gelen detaylı planı `TravelPlan` modeline `itinerary_data` olarak kaydeder.
  - Frontend'e hem kaydedilen planı hem itinerary JSON'unu döner.
- Endpointler için request/response serializer'ları tanımlandı.
- Tarih doğrulaması eklendi (`end_date >= start_date`).
- Hata yönetimi eklendi:
  - 400: doğrulama/iş kuralı hataları
  - 502: Gemini servis hataları

### URL Bağlantıları

- `api/urls.py` güncellendi.
- Eklenen rotalar:
  - `/api/suggest-cities/`
  - `/api/generate-plan/`

### Doğrulama

- `python manage.py check` çalıştırıldı.
- Sonuç: sistem kontrolü hatasız geçti.

## Adım 5

Bu adımda API dokümantasyonu güncellendi ve Swagger üzerinde daha anlaşılır hale getirildi.

### Yapılanlar

- `api/views.py` dosyasında OpenAPI şemaları genişletildi.
- `SuggestCitiesView` ve `GeneratePlanView` için:
  - `operation_id` tanımlandı.
  - Başarılı yanıt (`200` / `201`) şemaları netleştirildi.
  - Hata yanıtları (`400`, `502`) için standart `ErrorResponseSerializer` eklendi.
  - Gerçek kullanım senaryolarına uygun request/response örnekleri eklendi.
- Böylece `/api/docs/` ve `/api/redoc/` üzerinde endpointlerin:
  - beklediği payload,
  - döndüğü başarı çıktısı,
  - olası hata formatı
  açık şekilde görünür hale getirildi.