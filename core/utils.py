"""Helpers — audit logging, IP extraction."""
from .models import AuditLog


def get_client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_action(request, action, description=''):
    """Persist an action to the audit log."""
    user = request.user if request.user.is_authenticated else None
    AuditLog.objects.create(
        user=user,
        action=action,
        description=description,
        ip_address=get_client_ip(request),
    )
