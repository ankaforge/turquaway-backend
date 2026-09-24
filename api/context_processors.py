from django.conf import settings


def seo(request):
    site_url = getattr(settings, 'SITE_URL', 'https://turquaway.com').rstrip('/')
    path = request.path or '/'
    return {
        'SITE_URL': site_url,
        'CANONICAL_URL': f'{site_url}{path}',
        'OG_IMAGE_URL': f'{site_url}{settings.STATIC_URL}landing/turquaway-logo.png',
        'SEO_EMAIL': 'support@turquaway.com',
        'SEO_PHONE': '+90 532 655 5993',
    }
