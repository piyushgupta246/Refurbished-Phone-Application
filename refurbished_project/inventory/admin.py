# inventory/admin.py

from django.contrib import admin
from .models import Phone, Platform, Listing, Brand, Query

@admin.register(Phone)
class PhoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_price', 'condition', 'stock')
    search_fields = ('name', 'condition')
    list_filter = ('condition', 'stock')
    ordering = ('name',)

@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ('name', 'fee_percentage', 'fixed_fee')
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ('phone', 'platform', 'platform_price', 'platform_condition_category', 'is_listed')
    list_filter = ('platform', 'is_listed', 'platform_condition_category')
    search_fields = ('phone__name', 'platform__name')
    raw_id_fields = ('phone', 'platform') # Use raw_id_fields for ForeignKey to improve performance with many items

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Query)
class QueryAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'created_at')
    search_fields = ('name', 'email')
    list_filter = ('created_at',)
    ordering = ('-created_at',)
