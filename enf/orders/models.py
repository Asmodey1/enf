from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from main.models import Product, ProductSize


class Order(models.Model):
    # Подписи статусов видны в истории заказов (get_status_display), поэтому переводим их
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('shipped', _('Shipped')),
        ('delivered', _('Delivered')),
        ('cancelled', _('Cancelled')),
    )
    PAYMENT_PROVIDER_CHOICES = (
        ('stripe', 'Stripe'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='orders')
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=254)
    company = models.CharField(max_length=100, blank=True, null=True)
    # Длины как в профиле и в форме оформления: адрес длиннее 100 символов раньше ронял заказ ошибкой базы
    address1 = models.CharField(max_length=255, blank=True, null=True)
    address2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    province = models.CharField(max_length=100, blank=True, null=True)
    postal_code= models.CharField(max_length=20, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    special_instructions = models.TextField(blank=True, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_provider = models.CharField(max_length=20, choices=PAYMENT_PROVIDER_CHOICES, null=True, blank=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"Order {self.id} by {self.email}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name ='items')
    # PROTECT: удаление товара или размера не должно молча стирать позиции из уже оформленных заказов
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    size = models.ForeignKey(ProductSize, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)


    def __str__(self):
        return f"{self.product.name} - {self.size.size.name} ({self.quantity})"

    def get_total_price(self):
        return self.price * self.quantity
