from django.contrib import admin
from .models import Subscription

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name', 'product_name', 'price', 'is_active', 'current_period_start', 'current_period_end')
    list_filter = ('product_name', 'is_active')
