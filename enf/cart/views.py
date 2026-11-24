from django.shortcuts import get_object_or_404, redirect
from django.views.generic import View
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.db import transaction
from django.utils.translation import gettext as _
from main.models import Product, ProductSize
from .models import CartItem
from .forms import AddToCartForm


class CartMixin:
    def get_cart(self, request):
        # request.cart подставляет CartMiddleware; сама корзина создаётся при первом обращении
        return request.cart


def render_cart(request, cart, template='cart/cart_modal.html'):
    """Содержимое корзины — одинаковое после открытия, изменения количества и удаления позиции."""
    context = {
        'cart': cart,
        'cart_items': cart.items.select_related(
            'product',
            'product_size__size'
        ).order_by('-added_at')
    }
    return TemplateResponse(request, template, context)


class CartModalView(CartMixin, View):
    def get(self, request):
        return render_cart(request, self.get_cart(request))


class AddToCartView(CartMixin, View):
    @transaction.atomic
    def post(self, request, slug):
        cart = self.get_cart(request)
        product = get_object_or_404(Product, slug=slug)

        form = AddToCartForm(request.POST, product=product)

        if not form.is_valid():
            return JsonResponse({
                'error': _('Invalid form data'),
                'errors' : form.errors,
            }, status=400)

        size_id = form.cleaned_data['size_id']
        if size_id:
            product_size = get_object_or_404(
                ProductSize,
                id=size_id,
                product=product
            )
        else:
            # Было product.product_filter_size — такого атрибута нет, запрос падал с ошибкой 500
            product_size = product.product_sizes.filter(stock__gt=0).first()
            if not product_size:
                return JsonResponse({
                    'error': _('No sizes available for this product')
                }, status=400)
        quantity = form.cleaned_data['quantity']
        if product_size.stock < quantity:
            return JsonResponse({
                'error': _('Only %(count)s items available') % {'count': product_size.stock}
            }, status=400)
        existing_item = cart.items.filter(
            product=product,
            product_size=product_size,
        ).first()

        if existing_item:
            total_quantity = existing_item.quantity + quantity
            if total_quantity > product_size.stock:
                return JsonResponse({
                    'error': _('Cannot add %(quantity)s items. Only %(available)s more items can be added') % {
                        'quantity': quantity,
                        'available': product_size.stock - existing_item.quantity,
                    }

                }, status=400)
        cart_item = cart.add_product(product, product_size, quantity)

        if request.headers.get('HX-Request'):
            return redirect('cart:cart_modal')
        return JsonResponse({
            'success': True,
            'total_items': cart.total_items,
            'message': _('%(product)s added to cart') % {'product': product.name},
            'cart_items_id': cart_item.id,
        })


class UpdateCartItemView(CartMixin, View):
    @transaction.atomic
    def post(self, request, item_id):
        cart = self.get_cart(request)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        try:
            quantity = int(request.POST.get('quantity', 1))
        except ValueError:
            # «abc» вместо числа раньше роняло запрос с ошибкой 500
            quantity = None

        if quantity is None or quantity < 0:
            return JsonResponse({
                'error': _('Invalid quantity')
            }, status=400)

        if quantity == 0:
            cart_item.delete()
        else:
            if quantity > cart_item.product_size.stock:
                return JsonResponse({
                    'error': _('Only %(count)s items available') % {'count': cart_item.product_size.stock}
                }, status=400)

            cart_item.quantity = quantity
            cart_item.save()
        return render_cart(request, cart)


class RemoveCartItemView(CartMixin, View):
    def post(self, request, item_id):
        cart = self.get_cart(request)
        cart_item = cart.items.filter(id=item_id).first()
        if cart_item is None:
            return JsonResponse({
                'error': _('Item not found'),
            }, status=400)
        cart_item.delete()
        return render_cart(request, cart)


class CartCountView(CartMixin, View):
    def get(self, request):
        cart = self.get_cart(request)
        return JsonResponse({
            'total_items': cart.total_items,
            'subtotal': float(cart.subtotal),
        })


class ClearCartView(CartMixin, View):
    def post(self, request):
        cart = self.get_cart(request)
        cart.clear()

        if request.headers.get('HX-Request'):
            return TemplateResponse(request, 'cart/cart_empty.html', {'cart': cart})
        # Раньше этот return из-за отступа стоял внутри if после другого return и не выполнялся:
        # без HTMX вьюха возвращала None и падала с ошибкой 500
        return JsonResponse({
            'success': True,
            'message': _('Cart cleared'),
        })


class CartSummaryView(CartMixin, View):
    def get(self, request):
        return render_cart(request, self.get_cart(request), 'cart/cart_summary.html')
