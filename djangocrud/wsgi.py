# djangocrud/wsgi.py

import os
import django
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangocrud.settings')

application = get_wsgi_application()

# == Lógica para crear un superusuario automáticamente ==
try:
    from django.contrib.auth.models import User
    from django.db.utils import OperationalError

    username = "DrControl"
    password = "mandarina12"  # cámbialo a algo seguro
    email = "drcontrol@outlook.com"

    # Intentamos queryear la base de datos. Si la migración aún no está hecha, saltará OperationalError
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username, email, password)
        print(f"Superuser '{username}' creado automáticamente.")
    else:
        print(f"Superuser '{username}' ya existe. No se crea nada.")
except OperationalError:
    print("Omitiendo creación de superusuario, la base de datos no está lista (falta migrate).")
except Exception as e:
    print(f"Error creando superusuario: {e}")
