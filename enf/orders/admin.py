from django.contrib import admin
from django.utils.html import format_html
from  django.utils.safestring import mark_safe
from  .models import Order, OrderItem



class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('image_preview', 'product', 'size', 'quantity', 'price', 'get_total_price')
    # Состав оформленного заказа — история: правка позиций разошлась бы с суммой заказа и оплатой в Stripe
    readonly_fields = fields
    can_delete = False


    def has_add_permission(self, request, obj=None):
        return False



    def image_preview(self, obj):
        if obj.product.main_image:
            # format_html экранирует адрес картинки, а mark_safe с f-строкой вставлял его как есть
            return format_html('<img src="{}" style="max-height: 100px; max-width: 100px; object-fit: cover;">',
                               obj.product.main_image.url)
        return mark_safe('<span style="color: gray;">No image</span>')
    image_preview.short_description = 'Image'


    def get_total_price(self, obj):
        try:
            return obj.get_total_price()
        except TypeError:
            return mark_safe('<span style="color: red;">Invalid data</span>')
    get_total_price.short_description = 'Total Price'
        



@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id',  'user' , 'email', 'total_price', 'payment_provider', 'status', 'created_at', 'updated_at')
    # Фильтр по имени покупателя выводил в боковой панели список всех имён; для поиска по имени есть search_fields
    list_filter = ('status', 'payment_provider', 'created_at')
    search_fields = ('email','first_name', 'last_name')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'total_price', 'stripe_payment_intent_id')
    inlines = [OrderItemInline]


    fieldsets = (
        ('Order Information',{
        'fields' : ('user', 'first_name', 'last_name', 'email', 'company', 'address1', 'address2', 'city', 'country', 'province', 'postal_code',
                    'phone', 'special_instructions', 'total_price' )
                
        
        }),
        ('Payment and Status',{
            'fields': ('status', 'payment_provider', 'stripe_payment_intent_id',)
        }),
        ('Timestamps',{
            'fields': ('created_at', 'updated_at',),
            'classes':('collapse',)
        })
    )

    # В оформленном заказе данные покупателя — это история, их не правят; менять можно статус
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('user', 'first_name', 'last_name', 'email', 'company',
                                           'address1', 'address2', 'city', 'country', 'province', 'postal_code', 'phone')
        return self.readonly_fields