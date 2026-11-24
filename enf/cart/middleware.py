from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject
from .models import Cart



class CartMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Корзина создаётся при первом обращении к request.cart (добавление товара, открытие корзины),
        # а не на каждый запрос: раньше webhook Stripe, боты и запросы картинок плодили пустые сессии и корзины
        request.cart = SimpleLazyObject(lambda: Cart.for_request(request))
        return None
