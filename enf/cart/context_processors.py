from .models import Cart


def cart_processor(request):
    # Ради счётчика в шапке корзину не создаём: нет сессии или корзины — значит, она пуста
    session_key = request.session.session_key
    cart = Cart.objects.filter(session_key=session_key).first() if session_key else None
    return {
        'cart_total_items': cart.total_items if cart else 0,
    }
