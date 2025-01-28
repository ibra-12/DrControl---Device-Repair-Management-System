from django.urls import path
from . import views


urlpatterns = [
    # Rutas para la app 'tasks'
    path('', views.home, name='tasks_home'),
    path('lista/', views.tasks, name='tasks_list'),

    # ...
]