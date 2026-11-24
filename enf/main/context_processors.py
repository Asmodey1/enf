from .models import Category


def site(request):
    is_htmx = bool(request.headers.get('HX-Request'))
    return {
        'site_name': 'ENFANTS RICHES DÉPRIMÉS',
        'nav_categories': Category.objects.all(),
        'is_htmx': is_htmx,
        # HTMX вставляет ответ внутрь уже открытой страницы, поэтому обёртка base.html ему не нужна
        'base_template': 'main/partial.html' if is_htmx else 'main/base.html',
    }
