from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'country')
    list_filter = ('country',)
    # Между 'city' и 'country' не было запятой: Python склеивал их в 'citycountry', и поиск падал с ошибкой 500
    search_fields = ('email', 'first_name', 'last_name', 'company', 'city', 'country')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'company', 'address1', 'address2', 'city', 'country', 'province', 'postal_code', 'phone')
        }),
        ('Permissions', {
            'fields':('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {'fields':('last_login', 'date_joined')
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields':('email', 'first_name', 'last_name', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )



admin.site.register(CustomUser, CustomUserAdmin)
