from django.contrib import admin
from .models import Category, DiscountRule

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(DiscountRule)
class DiscountRuleAdmin(admin.ModelAdmin):
    list_display = ['rule_type', 'active', 'threshold', 'percentage', 'flat_amount', 'category', 'min_quantity']
    list_filter = ['rule_type', 'active']
    search_fields = ['rule_type']

