"""Role-based access decorators."""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    """Allow only admin / superuser."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not (request.user.is_admin() if hasattr(request.user, 'is_admin') else request.user.is_superuser):
            messages.error(request, 'You do not have permission to access that page.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped


def staff_or_admin_required(view_func):
    """Any authenticated user (staff or admin)."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped
