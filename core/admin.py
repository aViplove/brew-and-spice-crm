"""Django admin registrations."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (CustomUser, Shop, Customer, Product, Order, OrderItem,
                     FootfallEntry, Inventory, InventoryLog, AuditLog)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Brew & Spice', {'fields': ('role', 'phone', 'avatar')}),
    )


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'email', 'loyalty_points', 'created_at')
    search_fields = ('full_name', 'phone', 'email')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'available')
    list_filter = ('category', 'available')
    search_fields = ('name',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'staff', 'total', 'payment_method', 'created_at')
    list_filter = ('payment_method', 'created_at')
    inlines = [OrderItemInline]


@admin.register(FootfallEntry)
class FootfallAdmin(admin.ModelAdmin):
    list_display = ('entry_time', 'visitor_count', 'recorded_by')
    list_filter = ('entry_time',)


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'quantity', 'unit', 'minimum_stock', 'is_low_stock')


@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ('item', 'action', 'quantity_change', 'user', 'created_at')
    list_filter = ('action',)


@admin.register(AuditLog)
class AuditAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'ip_address')
    list_filter = ('action',)
    search_fields = ('user__username', 'description')


admin.site.register(Shop)
admin.site.site_header = 'Brew & Spice CRM'
admin.site.site_title = 'Brew & Spice'
admin.site.index_title = 'Coffee Shop Management'
