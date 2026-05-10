"""URL routes for the core app."""
from django.urls import path
from . import views

urlpatterns = [
    # auth
    path('', views.login_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # customers
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/add/', views.customer_create, name='customer_create'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('customers/<int:pk>/edit/', views.customer_edit, name='customer_edit'),
    path('customers/<int:pk>/delete/', views.customer_delete, name='customer_delete'),

    # products
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.product_create, name='product_create'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('products/<int:pk>/toggle/', views.product_toggle, name='product_toggle'),

    # orders
    path('orders/', views.order_list, name='order_list'),
    path('orders/new/', views.order_create, name='order_create'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),

    # footfall
    path('footfall/', views.footfall_list, name='footfall_list'),
    path('footfall/add/', views.footfall_create, name='footfall_create'),
    path('footfall/<int:pk>/delete/', views.footfall_delete, name='footfall_delete'),

    # inventory
    path('inventory/', views.inventory_list, name='inventory_list'),
    path('inventory/add/', views.inventory_create, name='inventory_create'),
    path('inventory/<int:pk>/edit/', views.inventory_edit, name='inventory_edit'),
    path('inventory/<int:pk>/adjust/', views.inventory_adjust, name='inventory_adjust'),
    path('inventory/<int:pk>/delete/', views.inventory_delete, name='inventory_delete'),

    # staff
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/add/', views.staff_create, name='staff_create'),
    path('staff/<int:pk>/edit/', views.staff_edit, name='staff_edit'),
    path('staff/<int:pk>/delete/', views.staff_delete, name='staff_delete'),

    # audit + settings
    path('audit-log/', views.audit_log, name='audit_log'),
    path('settings/', views.shop_settings, name='shop_settings'),

    # api
    path('api/today-stats/', views.api_today_stats, name='api_today_stats'),
]
