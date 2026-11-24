import stripe
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import translation
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from cart.views import CartMixin
from orders.models import Order
from orders.services import confirm_payment


#stripe login
#stripe listen --forward-to localhost:8000/payment/stripe/webhook/

stripe.api_key=settings.STRIPE_SECRET_KEY
stripe_endpoint_secret=settings.STRIPE_WEBKOOK_SECRET_KEY


def create_stripe_checkout_session(order, request):
    # Позиции берём из заказа, а не из корзины: списать нужно ровно то, что записано в заказе
    line_items = []
    for item in order.items.select_related('product', 'size__size'):
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': f'{item.product.name} - {item.size.size.name}',
                },
                'unit_amount': int(item.price * 100),
            },
            'quantity': item.quantity,
        })

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=line_items,
        mode='payment',
        success_url=request.build_absolute_uri(reverse('payment:stripe_success')) + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=request.build_absolute_uri(reverse('payment:stripe_cancel')) + f'?order_id={order.id}',
        metadata={
            'order_id': order.id,
            # Язык сайта на момент заказа: на нём придёт письмо-подтверждение
            'language': translation.get_language(),
        }
    )
    order.stripe_payment_intent_id = checkout_session.payment_intent
    order.payment_provider = 'stripe'
    order.save()
    return checkout_session



@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe_endpoint_secret
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    session = event['data']['object']
    if event['type'] == 'checkout.session.completed' and session.get('payment_status') == 'paid':
        order = confirm_payment(
            session['metadata'].get('order_id'),
            payment_intent_id=session.get('payment_intent'),
            language=session['metadata'].get('language'),
        )
        if order is None:
            return HttpResponse(status=400)

    elif event['type'] == 'checkout.session.expired':
        # Ссылка на оплату истекла (Stripe шлёт это через сутки): неоплаченный заказ больше не висит
        # в истории как «Ожидает оплаты», а честно отменяется
        order = Order.objects.filter(id=session['metadata'].get('order_id'), status='pending').first()
        if order:
            order.status = 'cancelled'
            order.save()

    return HttpResponse(status=200)



def stripe_success(request):
    session_id = request.GET.get('session_id')
    if not session_id:
        return redirect('main:index')

    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.InvalidRequestError:
        # Несуществующий session_id в адресе — это «не найдено», а не ошибка сервера
        raise Http404
    order_id = session.metadata.get('order_id')
    # Webhook может прийти позже или не дойти вовсе (локально без stripe listen),
    # поэтому подтверждаем оплату и здесь. Дважды она не засчитается
    if session.payment_status == 'paid':
        confirm_payment(order_id, payment_intent_id=session.payment_intent,
                        language=session.metadata.get('language'))
    order = get_object_or_404(Order, id=order_id)

    cart = CartMixin().get_cart(request)
    cart.clear()

    context = {'order': order}
    if request.headers.get('HX-Request'):
        return TemplateResponse(request, 'payment/stripe_success_content.html', context)
    return render(request, 'payment/stripe_success.html', context)


@login_required
def stripe_cancel(request):
    order_id = request.GET.get('order_id', '')
    if not order_id:
        return redirect('orders:checkout')
    if not order_id.isdigit():
        # ?order_id=abc раньше падало с ошибкой 500
        raise Http404

    # Ищем только среди своих заказов, иначе любой отменил бы чужой заказ, подставив номер в ссылку
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status == 'pending':
        order.status = 'cancelled'
        order.save()
    elif order.status != 'cancelled':
        # Заказ уже оплачен: отменять его нельзя, а страница «оплата отменена» была бы неправдой
        return redirect(reverse('users:profile') + '#orders')
    context = {'order': order}
    if request.headers.get('HX-Request'):
        return TemplateResponse(request, 'payment/stripe_cancel_content.html', context)
    return render(request, 'payment/stripe_cancel.html', context)
