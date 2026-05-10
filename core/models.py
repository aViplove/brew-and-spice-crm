"""
Database models for Brew & Spice CRM.

Models:
 - CustomUser   : Authentication w/ role (admin / staff)
 - Shop         : Shop / outlet info
 - Customer     : Cafe customers + loyalty
 - Product      : Menu items
 - Order        : Customer orders
 - OrderItem    : Line items in an order
 - FootfallEntry: Visitor / footfall tracking
 - Inventory    : Stock items
 - InventoryLog : History of stock movement
 - AuditLog     : Audit trail for important actions
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from decimal import Decimal


# ---------------------------------------------------------------------------
# 1. Custom user with role-based access
# ---------------------------------------------------------------------------
class CustomUser(AbstractUser):
    """Custom user with a role flag (admin / staff)."""
    ROLE_CHOICES = (
        ('admin', 'Super Admin'),
        ('staff', 'Staff'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='staff')
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    def is_admin(self):
        return self.role == 'admin' or self.is_superuser

    def is_staff_only(self):
        return self.role == 'staff' and not self.is_superuser

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


# ---------------------------------------------------------------------------
# 2. Shop info (single record kept; could support multiple outlets later)
# ---------------------------------------------------------------------------
class Shop(models.Model):
    name = models.CharField(max_length=100, default='Brew & Spice')
    tagline = models.CharField(max_length=200, default='Crafted with care, brewed with love.')
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    opening_time = models.TimeField(default='08:00')
    closing_time = models.TimeField(default='22:00')

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# 3. Customer
# ---------------------------------------------------------------------------
class Customer(models.Model):
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True)
    favorite_drink = models.CharField(max_length=100, blank=True)
    birthday = models.DateField(null=True, blank=True)
    loyalty_points = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='customers_added')

    class Meta:
        ordering = ['-created_at']

    @property
    def total_visits(self):
        """Total visits = number of orders placed by this customer."""
        return self.orders.count()

    @property
    def is_returning(self):
        return self.total_visits > 1

    @property
    def total_spent(self):
        return self.orders.aggregate(t=models.Sum('total'))['t'] or Decimal('0.00')

    def __str__(self):
        return f"{self.full_name} ({self.phone})"


# ---------------------------------------------------------------------------
# 4. Product menu
# ---------------------------------------------------------------------------
class Product(models.Model):
    CATEGORY_CHOICES = (
        ('coffee', 'Coffee'),
        ('tea', 'Tea'),
        ('snacks', 'Snacks'),
        ('desserts', 'Desserts'),
    )
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='coffee')
    price = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField(blank=True)
    available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} – ₹{self.price}"


# ---------------------------------------------------------------------------
# 5. Orders & items
# ---------------------------------------------------------------------------
class Order(models.Model):
    PAYMENT_CHOICES = (
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('upi', 'UPI'),
        ('wallet', 'Wallet'),
    )
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL,
                                 null=True, blank=True, related_name='orders')
    staff = models.ForeignKey(CustomUser, on_delete=models.SET_NULL,
                              null=True, blank=True, related_name='orders_processed')
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='cash')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def recalculate_total(self):
        """Recompute total from line items."""
        total = sum((i.subtotal for i in self.items.all()), Decimal('0.00'))
        self.total = total
        self.save(update_fields=['total'])
        return total

    def __str__(self):
        cust = self.customer.full_name if self.customer else 'Walk-in'
        return f"Order #{self.pk} – {cust} – ₹{self.total}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

    def save(self, *args, **kwargs):
        if not self.unit_price:
            self.unit_price = self.product.price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"


# ---------------------------------------------------------------------------
# 6. Footfall
# ---------------------------------------------------------------------------
class FootfallEntry(models.Model):
    entry_time = models.DateTimeField(default=timezone.now)
    exit_time = models.DateTimeField(null=True, blank=True)
    visitor_count = models.PositiveIntegerField(default=1)
    recorded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL,
                                    null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-entry_time']
        verbose_name_plural = 'Footfall entries'

    def __str__(self):
        return f"{self.visitor_count} visitors @ {self.entry_time:%Y-%m-%d %H:%M}"


# ---------------------------------------------------------------------------
# 7. Inventory
# ---------------------------------------------------------------------------
class Inventory(models.Model):
    UNIT_CHOICES = (
        ('kg', 'Kilogram'),
        ('g', 'Gram'),
        ('l', 'Liter'),
        ('ml', 'Milliliter'),
        ('pcs', 'Pieces'),
        ('pack', 'Pack'),
    )
    item_name = models.CharField(max_length=100, unique=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='pcs')
    minimum_stock = models.DecimalField(max_digits=10, decimal_places=2, default=10)
    vendor = models.CharField(max_length=120, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['item_name']
        verbose_name_plural = 'Inventory'

    @property
    def is_low_stock(self):
        return self.quantity <= self.minimum_stock

    def __str__(self):
        return f"{self.item_name} – {self.quantity}{self.unit}"


class InventoryLog(models.Model):
    ACTION_CHOICES = (
        ('add', 'Stock Added'),
        ('reduce', 'Stock Reduced'),
        ('adjust', 'Stock Adjusted'),
    )
    item = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    quantity_change = models.DecimalField(max_digits=10, decimal_places=2)
    new_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    note = models.CharField(max_length=255, blank=True)
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.item.item_name} {self.action} {self.quantity_change}"


# ---------------------------------------------------------------------------
# 8. Audit log
# ---------------------------------------------------------------------------
class AuditLog(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        u = self.user.username if self.user else 'system'
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {u}: {self.action}"
