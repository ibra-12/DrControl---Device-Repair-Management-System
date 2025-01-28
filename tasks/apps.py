from django.apps import AppConfig
from django.db.utils import OperationalError



class TasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tasks'

    def ready(self):
            # Se ejecuta cuando Django carga esta app
            try:
                from django.contrib.auth.models import User
                username = 'DrControl'
                if not User.objects.filter(username=username).exists():
                    User.objects.create_superuser(
                        username, 'drcontrol@outlook.com', 'Mandarina12'
                    )
            except OperationalError:
                pass