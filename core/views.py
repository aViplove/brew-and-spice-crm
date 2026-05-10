"""
Views for Brew & Spice CRM.
Auth, dashboard analytics, customers, products, orders, footfall, inventory.
"""
import json
from decimal import Decimal
from datetime import timedelta, datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, F, Q, DecimalField
from django.db.models.functions import TruncHour, TruncDate
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator

from .models import (CustomUser, Customer, Product, Order, OrderItem,
                     FootfallEntry, Inventory, InventoryLog, AuditLog)
from .forms import (StaffCreationForm, StaffEditForm, CustomerForm, ProductForm,
                    FootfallForm, InventoryForm, StockAdjustForm, ShopForm)
from .decorators import admin_required, staff_or_admin_required
from .utils import log_action


# ===========================================================================
# AUTH
# ===========================================================================
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            log_action(request, 'LOGIN', f'{user.username} logged in')
            return redirect('dashboard')
        messages.error(request, 'Invalid credentials. Please try again.')
    return render(request, 'registration/login.html')


@login_required
def logout_view(request):
    log_action(request, 'LOGOUT', f'{request.user.username} logged out')
    logout(request)
    return redirect('login')


# ===========================================================================
# DASHBOARD - real analytics from DB
# ===========================================================================
@login_required
def dashboard(request):
    now = timezone.localtime()
    today = now.date()
    week_ago = today - timedelta(days=6)

    # ---- KPI: today's footfall ------------------------------------------------
    today_footfall = FootfallEntry.objects.filter(
        entry_time__date=today
    ).aggregate(t=Sum('visitor_count'))['t'] or 0

    # ---- KPI: today's revenue -------------------------------------------------
    today_revenue = Order.objects.filter(
        created_at__date=today
    ).aggregate(t=Sum('total'))['t'] or Decimal('0.00')

    # ---- KPI: total customers -------------------------------------------------
    total_customers = Customer.objects.count()

    # ---- KPI: returning customers (>1 order) ----------------------------------
    returning_customers = Customer.objects.annotate(
        n=Count('orders')
    ).filter(n__gt=1).count()

    # ---- KPI: peak hour for today --------------------------------------------
    hour_counts = (FootfallEntry.objects
                   .filter(entry_time__date=today)
                   .annotate(h=TruncHour('entry_time'))
                   .values('h')
                   .annotate(total=Sum('visitor_count'))
                   .order_by('-total'))
    peak_hour_label = '—'
    if hour_counts:
        peak_h = timezone.localtime(hour_counts[0]['h']).hour
        peak_hour_label = f"{peak_h:02d}:00 – {(peak_h + 1) % 24:02d}:00"

    # ---- Chart: weekly footfall (last 7 days, line) --------------------------
    weekly_labels, weekly_data = [], []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        c = FootfallEntry.objects.filter(entry_time__date=d).aggregate(
            t=Sum('visitor_count'))['t'] or 0
        weekly_labels.append(d.strftime('%a %d'))
        weekly_data.append(int(c))

    # ---- Chart: hourly footfall today (bar) ----------------------------------
    hourly_data = [0] * 24
    for row in (FootfallEntry.objects
                .filter(entry_time__date=today)
                .annotate(h=TruncHour('entry_time'))
                .values('h')
                .annotate(total=Sum('visitor_count'))):
        h = timezone.localtime(row['h']).hour
        hourly_data[h] = int(row['total'])
    hourly_labels = [f"{h:02d}" for h in range(24)]

    # ---- Chart: top selling products (last 30 days) --------------------------
    month_ago = today - timedelta(days=30)
    top_products_qs = (OrderItem.objects
                       .filter(order__created_at__date__gte=month_ago)
                       .values('product__name')
                       .annotate(total_qty=Sum('quantity'))
                       .order_by('-total_qty')[:6])
    top_product_labels = [r['product__name'] for r in top_products_qs]
    top_product_data = [int(r['total_qty']) for r in top_products_qs]

    # ---- Chart: revenue trend (last 14 days) ---------------------------------
    revenue_labels, revenue_data = [], []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        rev = Order.objects.filter(created_at__date=d).aggregate(
            t=Sum('total'))['t'] or 0
        revenue_labels.append(d.strftime('%d %b'))
        revenue_data.append(float(rev))

    # ---- Heatmap: weekday x hour, last 4 weeks --------------------------------
    # rows = weekday (0=Mon..6=Sun), cols = hour (0..23)
    heatmap = [[0] * 24 for _ in range(7)]
    four_weeks_ago = today - timedelta(days=28)
    for fe in FootfallEntry.objects.filter(entry_time__date__gte=four_weeks_ago):
        local = timezone.localtime(fe.entry_time)
        # weekday(): Monday=0 ... Sunday=6
        heatmap[local.weekday()][local.hour] += fe.visitor_count

    # ---- Recent activity (latest orders for table) ---------------------------
    recent_orders = Order.objects.select_related('customer', 'staff').order_by('-created_at')[:8]

    # Low-stock items
    low_stock_items = Inventory.objects.filter(quantity__lte=F('minimum_stock'))[:5]

    context = {
        'today_footfall': today_footfall,
        'today_revenue': today_revenue,
        'total_customers': total_customers,
        'returning_customers': returning_customers,
        'peak_hour_label': peak_hour_label,

        'weekly_labels':  json.dumps(weekly_labels),
        'weekly_data':    json.dumps(weekly_data),
        'hourly_labels':  json.dumps(hourly_labels),
        'hourly_data':    json.dumps(hourly_data),
        'top_product_labels': json.dumps(top_product_labels),
        'top_product_data':   json.dumps(top_product_data),
        'revenue_labels': json.dumps(revenue_labels),
        'revenue_data':   json.dumps(revenue_data),
        'heatmap_data':   json.dumps(heatmap),

        'recent_orders': recent_orders,
        'low_stock_items': low_stock_items,
    }
    return render(request, 'core/dashboard.html', context)


# ===========================================================================
# CUSTOMERS
# ===========================================================================
@login_required
def customer_list(request):
    q = request.GET.get('q', '').strip()
    qs = Customer.objects.all()
    if q:
        qs = qs.filter(Q(full_name__icontains=q) | Q(phone__icontains=q) | Q(email__icontains=q))
    paginator = Paginator(qs, 15)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'core/customer_list.html', {'page': page, 'q': q})


@login_required
def customer_create(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            cust = form.save(commit=False)
            cust.created_by = request.user
            cust.save()
            log_action(request, 'CUSTOMER_CREATE', f'Added customer {cust.full_name}')
            messages.success(request, f'Customer "{cust.full_name}" added.')
            return redirect('customer_list')
    else:
        form = CustomerForm()
    return render(request, 'core/customer_form.html', {'form': form, 'title': 'Add Customer'})


@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            log_action(request, 'CUSTOMER_UPDATE', f'Updated customer {customer.full_name}')
            messages.success(request, 'Customer updated.')
            return redirect('customer_detail', pk=customer.pk)
    else:
        form = CustomerForm(instance=customer)
    return render(request, 'core/customer_form.html',
                  {'form': form, 'title': f'Edit {customer.full_name}'})


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    orders = customer.orders.all().order_by('-created_at')[:50]
    return render(request, 'core/customer_detail.html',
                  {'customer': customer, 'orders': orders})


@admin_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        name = customer.full_name
        customer.delete()
        log_action(request, 'CUSTOMER_DELETE', f'Deleted customer {name}')
        messages.success(request, f'Customer "{name}" deleted.')
        return redirect('customer_list')
    return render(request, 'core/confirm_delete.html',
                  {'object': customer, 'kind': 'customer',
                   'cancel_url': 'customer_list'})


# ===========================================================================
# PRODUCTS
# ===========================================================================
@login_required
def product_list(request):
    products = Product.objects.all()
    return render(request, 'core/product_list.html', {'products': products})


@admin_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            p = form.save()
            log_action(request, 'PRODUCT_CREATE', f'Created product {p.name}')
            messages.success(request, f'Product "{p.name}" added.')
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'core/product_form.html', {'form': form, 'title': 'Add Product'})


@admin_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            log_action(request, 'PRODUCT_UPDATE', f'Updated product {product.name}')
            messages.success(request, 'Product updated.')
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'core/product_form.html',
                  {'form': form, 'title': f'Edit {product.name}'})


@admin_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        n = product.name
        product.delete()
        log_action(request, 'PRODUCT_DELETE', f'Deleted product {n}')
        messages.success(request, f'Product "{n}" deleted.')
        return redirect('product_list')
    return render(request, 'core/confirm_delete.html',
                  {'object': product, 'kind': 'product', 'cancel_url': 'product_list'})


@admin_required
@require_POST
def product_toggle(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.available = not product.available
    product.save(update_fields=['available'])
    return JsonResponse({'available': product.available})


# ===========================================================================
# ORDERS
# ===========================================================================
@login_required
def order_list(request):
    qs = Order.objects.select_related('customer', 'staff').prefetch_related('items')
    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))

    today = timezone.localdate()
    today_revenue = Order.objects.filter(created_at__date=today).aggregate(
        t=Sum('total'))['t'] or 0
    today_orders = Order.objects.filter(created_at__date=today).count()

    return render(request, 'core/order_list.html',
                  {'page': page, 'today_revenue': today_revenue,
                   'today_orders': today_orders})


@login_required
def order_create(request):
    products = Product.objects.filter(available=True).order_by('category', 'name')
    customers = Customer.objects.all().order_by('full_name')

    if request.method == 'POST':
        customer_id = request.POST.get('customer') or None
        payment_method = request.POST.get('payment_method', 'cash')
        notes = request.POST.get('notes', '')

        # Items posted as item_<id>=qty (qty might be 0)
        items_to_create = []
        for prod in products:
            qty_raw = request.POST.get(f'item_{prod.id}', '0')
            try:
                qty = int(qty_raw)
            except ValueError:
                qty = 0
            if qty > 0:
                items_to_create.append((prod, qty))

        if not items_to_create:
            messages.error(request, 'Please add at least one item to the order.')
        else:
            order = Order.objects.create(
                customer_id=customer_id if customer_id else None,
                staff=request.user,
                payment_method=payment_method,
                notes=notes,
            )
            for prod, qty in items_to_create:
                OrderItem.objects.create(
                    order=order, product=prod,
                    quantity=qty, unit_price=prod.price)
            order.recalculate_total()

            # award loyalty pts: 1 pt per ₹100 spent
            if order.customer:
                pts = int(order.total // 100)
                if pts:
                    order.customer.loyalty_points = F('loyalty_points') + pts
                    order.customer.save(update_fields=['loyalty_points'])

            log_action(request, 'ORDER_CREATE',
                       f'Order #{order.id} – ₹{order.total}')
            messages.success(request, f'Order #{order.id} created – ₹{order.total}')
            return redirect('order_detail', pk=order.pk)

    return render(request, 'core/order_form.html',
                  {'products': products, 'customers': customers})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.select_related('customer', 'staff').prefetch_related('items__product'),
        pk=pk)
    return render(request, 'core/order_detail.html', {'order': order})


# ===========================================================================
# FOOTFALL
# ===========================================================================
@login_required
def footfall_list(request):
    today = timezone.localdate()
    qs = FootfallEntry.objects.select_related('recorded_by')
    paginator = Paginator(qs, 25)
    page = paginator.get_page(request.GET.get('page'))

    today_total = FootfallEntry.objects.filter(entry_time__date=today).aggregate(
        t=Sum('visitor_count'))['t'] or 0

    # peak hour today
    peak = (FootfallEntry.objects
            .filter(entry_time__date=today)
            .annotate(h=TruncHour('entry_time'))
            .values('h')
            .annotate(total=Sum('visitor_count'))
            .order_by('-total')
            .first())
    peak_hour = '—'
    if peak:
        h = timezone.localtime(peak['h']).hour
        peak_hour = f"{h:02d}:00 ({peak['total']} visitors)"

    return render(request, 'core/footfall_list.html',
                  {'page': page, 'today_total': today_total, 'peak_hour': peak_hour})


@login_required
def footfall_create(request):
    if request.method == 'POST':
        form = FootfallForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.recorded_by = request.user
            entry.save()
            log_action(request, 'FOOTFALL_CREATE',
                       f'Recorded {entry.visitor_count} visitors')
            messages.success(request, 'Footfall entry added.')
            return redirect('footfall_list')
    else:
        form = FootfallForm(initial={'entry_time': timezone.now()})
    return render(request, 'core/footfall_form.html', {'form': form})


@admin_required
def footfall_delete(request, pk):
    entry = get_object_or_404(FootfallEntry, pk=pk)
    if request.method == 'POST':
        entry.delete()
        messages.success(request, 'Footfall entry removed.')
        return redirect('footfall_list')
    return render(request, 'core/confirm_delete.html',
                  {'object': entry, 'kind': 'footfall entry',
                   'cancel_url': 'footfall_list'})


# ===========================================================================
# INVENTORY
# ===========================================================================
@login_required
def inventory_list(request):
    items = Inventory.objects.all()
    low_stock = items.filter(quantity__lte=F('minimum_stock'))
    return render(request, 'core/inventory_list.html',
                  {'items': items, 'low_stock_count': low_stock.count()})


@admin_required
def inventory_create(request):
    if request.method == 'POST':
        form = InventoryForm(request.POST)
        if form.is_valid():
            item = form.save()
            InventoryLog.objects.create(
                item=item, action='add',
                quantity_change=item.quantity,
                new_quantity=item.quantity,
                user=request.user, note='Initial stock')
            log_action(request, 'INVENTORY_CREATE', f'Added item {item.item_name}')
            messages.success(request, 'Inventory item added.')
            return redirect('inventory_list')
    else:
        form = InventoryForm()
    return render(request, 'core/inventory_form.html',
                  {'form': form, 'title': 'Add Item'})


@admin_required
def inventory_edit(request, pk):
    item = get_object_or_404(Inventory, pk=pk)
    if request.method == 'POST':
        form = InventoryForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            log_action(request, 'INVENTORY_UPDATE', f'Updated item {item.item_name}')
            messages.success(request, 'Inventory item updated.')
            return redirect('inventory_list')
    else:
        form = InventoryForm(instance=item)
    return render(request, 'core/inventory_form.html',
                  {'form': form, 'title': f'Edit {item.item_name}'})


@login_required
def inventory_adjust(request, pk):
    item = get_object_or_404(Inventory, pk=pk)
    if request.method == 'POST':
        form = StockAdjustForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            amt = form.cleaned_data['amount']
            note = form.cleaned_data['note']
            if action == 'add':
                item.quantity += amt
                qty_change = amt
            else:
                item.quantity = max(Decimal('0'), item.quantity - amt)
                qty_change = -amt
            item.save()
            InventoryLog.objects.create(
                item=item, action=action,
                quantity_change=qty_change,
                new_quantity=item.quantity,
                user=request.user, note=note)
            log_action(request, 'INVENTORY_ADJUST',
                       f'{action} {amt}{item.unit} on {item.item_name}')
            messages.success(request, f'Stock {action}ed.')
            return redirect('inventory_list')
    else:
        form = StockAdjustForm()
    logs = item.logs.select_related('user')[:20]
    return render(request, 'core/inventory_adjust.html',
                  {'form': form, 'item': item, 'logs': logs})


@admin_required
def inventory_delete(request, pk):
    item = get_object_or_404(Inventory, pk=pk)
    if request.method == 'POST':
        n = item.item_name
        item.delete()
        log_action(request, 'INVENTORY_DELETE', f'Deleted {n}')
        messages.success(request, 'Inventory item deleted.')
        return redirect('inventory_list')
    return render(request, 'core/confirm_delete.html',
                  {'object': item, 'kind': 'inventory item',
                   'cancel_url': 'inventory_list'})


# ===========================================================================
# STAFF MANAGEMENT (admin only)
# ===========================================================================
@admin_required
def staff_list(request):
    staff = CustomUser.objects.all().order_by('-date_joined')
    return render(request, 'core/staff_list.html', {'staff': staff})


@admin_required
def staff_create(request):
    if request.method == 'POST':
        form = StaffCreationForm(request.POST)
        if form.is_valid():
            u = form.save()
            log_action(request, 'STAFF_CREATE', f'Created user {u.username}')
            messages.success(request, f'Staff "{u.username}" created.')
            return redirect('staff_list')
    else:
        form = StaffCreationForm()
    return render(request, 'core/staff_form.html',
                  {'form': form, 'title': 'Add Staff Member'})


@admin_required
def staff_edit(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        form = StaffEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Staff updated.')
            return redirect('staff_list')
    else:
        form = StaffEditForm(instance=user)
    return render(request, 'core/staff_form.html',
                  {'form': form, 'title': f'Edit {user.username}'})


@admin_required
def staff_delete(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    if user == request.user:
        messages.error(request, "You can't delete your own account.")
        return redirect('staff_list')
    if request.method == 'POST':
        n = user.username
        user.delete()
        log_action(request, 'STAFF_DELETE', f'Deleted user {n}')
        messages.success(request, f'User "{n}" deleted.')
        return redirect('staff_list')
    return render(request, 'core/confirm_delete.html',
                  {'object': user, 'kind': 'staff member',
                   'cancel_url': 'staff_list'})


# ===========================================================================
# AUDIT LOG (admin only)
# ===========================================================================
@admin_required
def audit_log(request):
    qs = AuditLog.objects.select_related('user').all()
    paginator = Paginator(qs, 30)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'core/audit_log.html', {'page': page})


# ===========================================================================
# SHOP SETTINGS
# ===========================================================================
@admin_required
def shop_settings(request):
    from .models import Shop
    shop = Shop.objects.first() or Shop.objects.create()
    if request.method == 'POST':
        form = ShopForm(request.POST, instance=shop)
        if form.is_valid():
            form.save()
            messages.success(request, 'Shop settings updated.')
            return redirect('shop_settings')
    else:
        form = ShopForm(instance=shop)
    return render(request, 'core/shop_settings.html', {'form': form})


# ===========================================================================
# AJAX endpoints
# ===========================================================================
@login_required
def api_today_stats(request):
    """Lightweight JSON endpoint for live dashboard refresh."""
    today = timezone.localdate()
    return JsonResponse({
        'footfall': FootfallEntry.objects.filter(entry_time__date=today).aggregate(
            t=Sum('visitor_count'))['t'] or 0,
        'revenue': float(Order.objects.filter(created_at__date=today).aggregate(
            t=Sum('total'))['t'] or 0),
        'orders':  Order.objects.filter(created_at__date=today).count(),
    })
