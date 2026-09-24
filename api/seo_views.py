from django.conf import settings
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET


def _site_url():
    return getattr(settings, 'SITE_URL', 'https://turquaway.com').rstrip('/')


@require_GET
def robots_txt(_request):
    site_url = _site_url()
    body = (
        'User-agent: *\n'
        'Allow: /\n'
        'Disallow: /admin/\n'
        'Disallow: /api/\n'
        'Disallow: /account/\n'
        'Disallow: /partner/\n'
        'Disallow: /login/\n'
        'Disallow: /register/\n'
        '\n'
        f'Sitemap: {site_url}/sitemap.xml\n'
    )
    return HttpResponse(body, content_type='text/plain; charset=utf-8')


@require_GET
def sitemap_xml(_request):
    site_url = _site_url()
    today = timezone.now().date().isoformat()
    entries = [
        (reverse('landing'), 'weekly', '1.0'),
        (reverse('about'), 'monthly', '0.8'),
        (reverse('privacy'), 'yearly', '0.4'),
        (reverse('terms'), 'yearly', '0.4'),
        (reverse('demo-apk'), 'monthly', '0.5'),
    ]
    urls = []
    for path, changefreq, priority in entries:
        urls.append(
            '  <url>\n'
            f'    <loc>{site_url}{path}</loc>\n'
            f'    <lastmod>{today}</lastmod>\n'
            f'    <changefreq>{changefreq}</changefreq>\n'
            f'    <priority>{priority}</priority>\n'
            '  </url>'
        )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + '\n'.join(urls)
        + '\n</urlset>\n'
    )
    return HttpResponse(xml, content_type='application/xml; charset=utf-8')
