import logging
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template.response import TemplateResponse
from django.utils.translation import gettext as _
from django.views.generic import View

from cart.views import CartMixin
from payment.views import create_stripe_checkout_session
from .forms import OrderForm
from .models import Order, OrderItem
from .services import find_stock_problems

logger = logging.getLogger(__name__)

# Подключена только оплата картой через Stripe. Раньше пропускался и 'heleket', для которого
# нет кода оплаты: заказ создавался, а вьюха ничего не возвращала и падала с ошибкой 500
PAYMENT_PROVIDERS = ('stripe',)


class CheckoutView(LoginRequiredMixin, CartMixin, View):
    def render_checkout(self, request, cart, form, error_message=''):
        context = {
            'form': form,
            'cart': cart,
            'cart_items': cart.items.select_related('product', 'product_size__size').order_by('-added_at'),
            'total_price': cart.subtotal,
            'error_message': error_message,
        }
        if request.headers.get('HX-Request'):
            return TemplateResponse(request, 'orders/checkout_content.html', context)
        return render(request, 'orders/checkout.html', context)

    def get(self, request):
        cart = self.get_cart(request)
        if cart.total_items == 0:
            return TemplateResponse(request, 'orders/empty_cart.html', {'message': _('Your cart is empty')})

        # Если что-то из корзины уже раскупили, предупреждаем сразу, а не после заполнения формы
        return self.render_checkout(request, cart, OrderForm(user=request.user),
                                    ' '.join(find_stock_problems(cart)))

    def post(self, request):
        cart = self.get_cart(request)
        if cart.total_items == 0:
            return TemplateResponse(request, 'orders/empty_cart.html', {'message': _('Your cart is empty')})

        form_data = request.POST.copy()
        # Поле email на странице только для чтения: заказ всегда оформляется на почту аккаунта,
        # даже если значение подменили в браузере
        form_data['email'] = request.user.email
        form = OrderForm(form_data, user=request.user)

        payment_provider = request.POST.get('payment_provider')
        if payment_provider not in PAYMENT_PROVIDERS:
            logger.warning('Invalid or missing payment provider: %s', payment_provider)
            # Форма с введёнными данными, а не пустая, как раньше
            return self.render_checkout(request, cart, form, _('Please select a payment method.'))

        if not form.is_valid():
            logger.warning('Form validation error: %s', form.errors)
            return self.render_checkout(request, cart, form, _('Please correct the errors in the form.'))

        # Пока товар лежал в корзине, его могли раскупить — не отправляем на оплату то, чего нет на складе
        stock_problems = find_stock_problems(cart)
        if stock_problems:
            return self.render_checkout(request, cart, form, ' '.join(stock_problems))

        order = Order.objects.create(
            user=request.user,
            first_name=form.cleaned_data['first_name'],
            last_name=form.cleaned_data['last_name'],
            email=form.cleaned_data['email'],
            company=form.cleaned_data['company'],
            address1=form.cleaned_data['address1'],
            address2=form.cleaned_data['address2'],
            city=form.cleaned_data['city'],
            country=form.cleaned_data['country'],
            province=form.cleaned_data['province'],
            postal_code=form.cleaned_data['postal_code'],
            phone=form.cleaned_data['phone'],
            special_instructions='',
            total_price=cart.subtotal,
            payment_provider=payment_provider,
        )

        for item in cart.items.select_related('product', 'product_size'):
            OrderItem.objects.create(
                order=order,
                product=item.product,
                size=item.product_size,
                quantity=item.quantity,
                price=item.product.price or Decimal('0.00')
            )

        try:
            checkout_session = create_stripe_checkout_session(order, request)
        except Exception as e:
            logger.error('Error creating payment: %s', e, exc_info=True)
            order.delete()
            return self.render_checkout(request, cart, form,
                                        _('Payment processing error: %(error)s') % {'error': e})

        # Корзину здесь не очищаем: если клиент вернётся со Stripe без оплаты, товары должны остаться.
        # Её очищает stripe_success, когда оплата прошла
        if request.headers.get('HX-Request'):
            response = HttpResponse(status=200)
            response['HX-Redirect'] = checkout_session.url
            return response
        return redirect(checkout_session.url)
