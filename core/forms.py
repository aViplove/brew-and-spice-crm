"""Forms used across the CRM."""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import (CustomUser, Customer, Product, Order, FootfallEntry,
                     Inventory, Shop)


class StaffCreationForm(UserCreationForm):
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES)
    phone = forms.CharField(max_length=20, required=False)
    first_name = forms.CharField(max_length=80, required=False)
    last_name = forms.CharField(max_length=80, required=False)
    email = forms.EmailField(required=False)

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'phone',
                  'role', 'password1', 'password2')


class StaffEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'phone',
                  'role', 'is_active')


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ('full_name', 'phone', 'email', 'favorite_drink',
                  'birthday', 'loyalty_points', 'notes')
        widgets = {
            'birthday': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ('name', 'category', 'price', 'description', 'available', 'image')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class FootfallForm(forms.ModelForm):
    class Meta:
        model = FootfallEntry
        fields = ('entry_time', 'exit_time', 'visitor_count', 'notes')
        widgets = {
            'entry_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'exit_time':  forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ('item_name', 'quantity', 'unit', 'minimum_stock', 'vendor')


class StockAdjustForm(forms.Form):
    ACTION_CHOICES = (
        ('add', 'Add stock'),
        ('reduce', 'Reduce stock'),
    )
    action = forms.ChoiceField(choices=ACTION_CHOICES)
    amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    note = forms.CharField(max_length=255, required=False)


class ShopForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = ('name', 'tagline', 'address', 'phone', 'email',
                  'opening_time', 'closing_time')
        widgets = {
            'opening_time': forms.TimeInput(attrs={'type': 'time'}),
            'closing_time': forms.TimeInput(attrs={'type': 'time'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }
