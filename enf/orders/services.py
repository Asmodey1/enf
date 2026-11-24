import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import gettext as _

from main.models import ProductSize
from .models import Order

logger = logging.getLogger(__name__)

# Из этих статусов заказ можно перевести в «оплачен». cancelled тоже: клиент мог нажать «назад»
# на странице Stripe (заказ отменился), а потом вернуться на неё и всё-таки заплатить
PAYABLE_STATUSES = ('pending', 'cancelled')


def find_stock_problems(cart):
    """Сообщения о позициях корзины, которых на складе меньше, чем хочет купить клиент."""
    problems = []
    for item in cart.items.select_related('product', 'product_size__size'):
        stock = item.product_size.stock
        if item.quantity <= stock:
            continue
        params = {'product': item.product.name, 'size': item.product_size.size.name, 'count': stock}
        if stock == 0:
            problems.append(_('%(product)s, size %(size)s, is sold out. Please remove it from your cart.') % params)
        else:
            problems.append(_('%(product)s, size %(size)s: only %(count)s left. Please reduce the quantity in your cart.') % params)
    return problems


def confirm_payment(order_id, payment_intent_id=None, language=None):
    """Отмечает заказ оплаченным, списывает остатки и отправляет клиенту письмо.

    Вызывается и из webhook Stripe, и со страницы успешной оплаты — что сработает раньше.
    Повторный вызов ничего не делает, поэтому остатки не спишутся дважды.
    """
    with transaction.atomic():
        # select_for_update: если webhook и страница успеха придут одновременно, второй подождёт первого
        order = Order.objects.select_for_update().filter(id=order_id).first()
        if order is None or order.status not in PAYABLE_STATUSES:
            return order

        for item in order.items.select_related('product'):
            product_size = ProductSize.objects.select_for_update().get(pk=item.size_id)
            if product_size.stock < item.quantity:
                # Последний экземпляр успели оплатить двое: деньги уже списаны, разбираться менеджеру
                logger.warning('Order %s: not enough stock for %s (product size %s): %s left, %s paid',
                               order.id, item.product.name, product_size.pk, product_size.stock, item.quantity)
            product_size.stock = max(product_size.stock - item.quantity, 0)
            product_size.save(update_fields=['stock'])

        order.status = 'processing'
        if payment_intent_id:
            order.stripe_payment_intent_id = payment_intent_id
        order.save()
        # Письмо уходит только после сохранения транзакции, чтобы не подтвердить то, что откатилось
        transaction.on_commit(lambda: send_order_confirmation(order, language))
    return order


def send_order_confirmation(order, language=None):
    """Письмо об оплаченном заказе. Сбой почты не должен ломать подтверждение оплаты."""
    with translation.override(language or settings.LANGUAGE_CODE):
        subject = _('Order #%(id)s is paid') % {'id': order.id}
        message = render_to_string('orders/emails/order_paid.txt', {'order': order})
    try:
        send_mail(subject, message, None, [order.email])
    except Exception:
        logger.exception('Could not send the confirmation email for order %s', order.id)
