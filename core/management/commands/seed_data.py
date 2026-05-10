"""
Seed sample data for Brew & Spice.

Usage:  python manage.py seed_data
"""
import random
from datetime import timedelta, time
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

from core.models import (Shop, Customer, Product, Order, OrderItem,
                         FootfallEntry, Inventory, InventoryLog)

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds the database with realistic sample data for Brew & Spice.'

    def handle(self, *args, **opts):
        self.stdout.write(self.style.MIGRATE_HEADING('Seeding Brew & Spice...'))

        # ---------- Shop --------------------------------------------------
        shop, _ = Shop.objects.get_or_create(
            id=1,
            defaults=dict(
                name='Brew & Spice',
                tagline='Crafted with care, brewed with love.',
                address='42 Cyber Hub, Sector 29, Gurugram, Haryana',
                phone='+91 98765 43210',
                email='hello@brewandspice.in',
                opening_time=time(8, 0),
                closing_time=time(22, 0),
            ))
        self.stdout.write(f'  ✓ Shop: {shop.name}')

        # ---------- Users -------------------------------------------------
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin', email='admin@brewandspice.in',
                password='admin123', role='admin', first_name='Aarav', last_name='Mehta')
            self.stdout.write('  ✓ Admin user (admin / admin123)')

        if not User.objects.filter(username='barista').exists():
            User.objects.create_user(
                username='barista', email='barista@brewandspice.in',
                password='staff123', role='staff', first_name='Riya', last_name='Sharma')
            self.stdout.write('  ✓ Staff user (barista / staff123)')

        if not User.objects.filter(username='cashier').exists():
            User.objects.create_user(
                username='cashier', email='cashier@brewandspice.in',
                password='staff123', role='staff', first_name='Karan', last_name='Patel')
            self.stdout.write('  ✓ Staff user (cashier / staff123)')

        admin_user = User.objects.get(username='admin')
        staff_users = list(User.objects.filter(role='staff'))

        # ---------- Products ----------------------------------------------
        Product.objects.all().delete()
        product_data = [
            # coffee
            ('Espresso',           'coffee',   140, 'Bold single shot of pure espresso.'),
            ('Cappuccino',         'coffee',   220, 'Espresso, steamed milk, velvet foam.'),
            ('Latte',              'coffee',   240, 'Smooth espresso with steamed milk.'),
            ('Americano',          'coffee',   180, 'Espresso lengthened with hot water.'),
            ('Mocha',              'coffee',   260, 'Chocolate, espresso, steamed milk.'),
            ('Cold Brew',          'coffee',   270, 'Slow-steeped, smooth and strong.'),
            ('Spiced Filter Kaapi','coffee',   200, 'South-Indian filter coffee with cardamom.'),
            # tea
            ('Masala Chai',        'tea',      120, 'House blend of spices, milk, and Assam tea.'),
            ('Kashmiri Kahwa',     'tea',      180, 'Saffron, almonds, green tea.'),
            ('Lemon Iced Tea',     'tea',      150, 'Fresh-brewed black tea, lemon, mint.'),
            ('Matcha Latte',       'tea',      280, 'Premium ceremonial-grade matcha.'),
            # snacks
            ('Veg Sandwich',       'snacks',   180, 'Grilled paneer, peppers, mint chutney.'),
            ('Croissant',          'snacks',   160, 'Buttery, flaky, baked fresh daily.'),
            ('Samosa Chaat',       'snacks',   140, 'Crispy samosa, chutneys, pomegranate.'),
            ('Avocado Toast',      'snacks',   320, 'Sourdough, avocado, chilli flakes.'),
            # desserts
            ('Tiramisu',           'desserts', 280, 'Classic Italian, dusted with cocoa.'),
            ('Chocolate Brownie',  'desserts', 220, 'Warm, gooey, with vanilla ice cream.'),
            ('Cheesecake',         'desserts', 260, 'New York-style, berry compote.'),
            ('Gulab Jamun Cake',   'desserts', 240, 'Fusion sponge cake with rabri.'),
        ]
        products = []
        for name, cat, price, desc in product_data:
            p = Product.objects.create(
                name=name, category=cat, price=Decimal(price), description=desc)
            products.append(p)
        self.stdout.write(f'  ✓ {len(products)} products')

        # ---------- Customers ---------------------------------------------
        Customer.objects.all().delete()
        customer_data = [
            ('Aarav Mehta',     '9876543210', 'aarav@example.com',  'Cappuccino'),
            ('Priya Singh',     '9876543211', 'priya@example.com',  'Masala Chai'),
            ('Rohan Kapoor',    '9876543212', 'rohan@example.com',  'Cold Brew'),
            ('Ananya Iyer',     '9876543213', 'ananya@example.com', 'Matcha Latte'),
            ('Vikram Joshi',    '9876543214', 'vikram@example.com', 'Espresso'),
            ('Neha Gupta',      '9876543215', 'neha@example.com',   'Latte'),
            ('Arjun Reddy',     '9876543216', 'arjun@example.com',  'Mocha'),
            ('Saanvi Verma',    '9876543217', 'saanvi@example.com', 'Kashmiri Kahwa'),
            ('Kabir Khanna',    '9876543218', 'kabir@example.com',  'Americano'),
            ('Diya Malhotra',   '9876543219', 'diya@example.com',   'Cappuccino'),
            ('Ishaan Bose',     '9876543220', 'ishaan@example.com', 'Spiced Filter Kaapi'),
            ('Myra Chopra',     '9876543221', 'myra@example.com',   'Lemon Iced Tea'),
        ]
        customers = []
        for name, phone, email, drink in customer_data:
            c = Customer.objects.create(
                full_name=name, phone=phone, email=email,
                favorite_drink=drink, created_by=admin_user,
                loyalty_points=random.randint(0, 200))
            customers.append(c)
        self.stdout.write(f'  ✓ {len(customers)} customers')

        # ---------- Footfall (last 30 days, with realistic peaks) ---------
        FootfallEntry.objects.all().delete()
        now = timezone.now()
        # peak hours: 9 (breakfast), 13 (lunch), 18 (evening)
        peak_hours = {8, 9, 10, 12, 13, 17, 18, 19, 20}
        slow_hours = {15, 16, 21}
        ff_count = 0
        for day_offset in range(30):
            day = (now - timedelta(days=day_offset)).date()
            is_weekend = day.weekday() >= 5
            for hour in range(8, 22):
                if hour in peak_hours:
                    base = random.randint(8, 15)
                elif hour in slow_hours:
                    base = random.randint(2, 5)
                else:
                    base = random.randint(4, 9)
                if is_weekend:
                    base = int(base * 1.4)
                # split into a few entries per hour
                remaining = base
                while remaining > 0:
                    chunk = min(remaining, random.randint(1, 4))
                    naive_dt = timezone.datetime.combine(
                        day, time(hour, random.randint(0, 59)))
                    entry_dt = timezone.make_aware(
                        naive_dt, timezone.get_current_timezone())
                    FootfallEntry.objects.create(
                        entry_time=entry_dt,
                        visitor_count=chunk,
                        recorded_by=random.choice(staff_users) if staff_users else admin_user)
                    remaining -= chunk
                    ff_count += 1
        self.stdout.write(f'  ✓ {ff_count} footfall entries (last 30 days)')

        # ---------- Orders -----------------------------------------------
        Order.objects.all().delete()
        payment_choices = ['cash', 'card', 'upi', 'upi', 'upi', 'wallet']  # weighted
        order_count = 0
        for day_offset in range(30):
            day = (now - timedelta(days=day_offset)).date()
            num_orders = random.randint(15, 35)
            for _ in range(num_orders):
                hour = random.choices(
                    population=list(range(8, 22)),
                    weights=[3, 8, 10, 6, 4, 9, 11, 5, 4, 7, 9, 10, 6, 3]
                )[0]
                ts = timezone.make_aware(
                    timezone.datetime.combine(day, time(hour, random.randint(0, 59))),
                    timezone.get_current_timezone())
                cust = random.choice(customers + [None] * 3)  # ~25% walk-ins
                order = Order.objects.create(
                    customer=cust,
                    staff=random.choice(staff_users) if staff_users else admin_user,
                    payment_method=random.choice(payment_choices),
                    created_at=ts,
                )
                # 1–4 items per order
                for prod in random.sample(products, random.randint(1, 4)):
                    OrderItem.objects.create(
                        order=order, product=prod,
                        quantity=random.randint(1, 3),
                        unit_price=prod.price)
                order.recalculate_total()
                order_count += 1
        self.stdout.write(f'  ✓ {order_count} orders')

        # ---------- Inventory --------------------------------------------
        Inventory.objects.all().delete()
        inv_data = [
            ('Coffee Beans (Arabica)', 25, 'kg',  10, 'Highland Roasters'),
            ('Coffee Beans (Robusta)', 18, 'kg',  10, 'Highland Roasters'),
            ('Whole Milk',             40, 'l',   20, 'Daily Dairy Co.'),
            ('Almond Milk',             8, 'l',    5, 'Plant Pure'),
            ('Sugar',                  30, 'kg',  10, 'Sweet Supply'),
            ('Tea Leaves (Assam)',      6, 'kg',   3, 'Tea Trails'),
            ('Matcha Powder',           2, 'kg',   1, 'Kyoto Imports'),
            ('Paper Cups (12oz)',     800, 'pcs', 200, 'EcoPack'),
            ('Croissant Dough',         3, 'kg',   2, 'Bakers Hub'),
            ('Cocoa Powder',            4, 'kg',   2, 'Sweet Supply'),
            ('Vanilla Syrup',           5, 'l',    3, 'Flavor House'),
        ]
        for name, qty, unit, min_s, vendor in inv_data:
            item = Inventory.objects.create(
                item_name=name, quantity=Decimal(qty), unit=unit,
                minimum_stock=Decimal(min_s), vendor=vendor)
            InventoryLog.objects.create(
                item=item, action='add',
                quantity_change=Decimal(qty),
                new_quantity=Decimal(qty),
                user=admin_user, note='Initial stock')
        self.stdout.write(f'  ✓ {len(inv_data)} inventory items')

        self.stdout.write(self.style.SUCCESS('\n✅ Seeding complete!\n'))
        self.stdout.write('  Admin login:  admin / admin123')
        self.stdout.write('  Staff login:  barista / staff123\n')
