"""Adds the Shop record + role flag to every template context."""
from .models import Shop


def shop_context(request):
    shop = Shop.objects.first()
    if not shop:
        shop = Shop.objects.create()
    is_admin_user = False
    if request.user.is_authenticated:
        is_admin_user = request.user.is_admin() if hasattr(request.user, 'is_admin') else request.user.is_superuser
    return {
        'shop': shop,
        'is_admin_user': is_admin_user,
    }
