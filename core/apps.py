from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Brew & Spice CRM'

    def ready(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # Create admin user
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                password='admin123'
            )

        # Create staff user
        if not User.objects.filter(username='barista').exists():
            user = User.objects.create_user(
                username='barista',
                password='staff123'
            )
            user.is_staff = True
            user.save()