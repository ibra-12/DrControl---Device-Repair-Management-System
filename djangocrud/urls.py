# Configuración de URLs del proyecto

from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from tasks import views as tasks_views  # Importamos las vistas de 'tasks' con un alias
from tasks.views import device_detail, edit_device, complete_repair, parts_list, add_part, edit_part, delete_part
from tasks.views import (
    customers_list,
    add_customer,
    edit_customer,
    delete_customer,
    customer_devices,
    finances_view
)

urlpatterns = [
    path('admin/', admin.site.urls),
    # Rutas para AJAX
    path('ajax/check_phone/', tasks_views.check_phone, name='check_phone'),

    # -- Rutas principales --
    path('', tasks_views.home, name='home'),
    path('signup/', tasks_views.signup, name='signup'),
    path('signin/', tasks_views.signin, name='signin'),
    path('logout/', tasks_views.signout, name='logout'),

    # -- Tareas (Tasks) --
    path('tasks/', tasks_views.tasks, name='tasks'),
    path('tasks/home/', tasks_views.tasks_home, name='tasks_home'),
    path('tasks_completed/', tasks_views.tasks_completed, name='tasks_completed'),
    path('tasks/create/', tasks_views.create_tasks, name='create_tasks'),
    path('tasks/<int:task_id>/', tasks_views.task_detail, name='task_detail'),
    path('tasks/<int:task_id>/complete', tasks_views.complete_task, name='complete_task'),
    path('tasks/<int:task_id>/delete', tasks_views.delete_task, name='delete_task'),

    # -- Dispositivos (Devices) --
    path('devices/', tasks_views.devices_home, name='devices_home'),
    path('devices/register/', tasks_views.register_device, name='register_device'),
    path('devices/queue/', tasks_views.repair_queue, name='repair_queue'),
    path('devices/in-progress/', tasks_views.devices_in_progress, name='devices_in_progress'),
    path('devices/ready/', tasks_views.devices_ready, name='devices_ready'),
    path('devices/delivered/', tasks_views.devices_delivered, name='devices_delivered'),
    path('devices/<int:device_id>/', device_detail, name='device_detail'),
    path('devices/<int:device_id>/complete_repair/', complete_repair, name='complete_repair'),
    path('devices/<int:device_id>/edit/', edit_device, name='edit_device'),
    path('public/<int:device_id>/', tasks_views.public_device_detail, name='public_device_detail'),
    
    #parts
    path('parts/', parts_list, name='parts_list'),
    path('parts/add/', add_part, name='add_part'),
    path('parts/<int:part_id>/edit/', edit_part, name='edit_part'),
    path('parts/<int:part_id>/delete/', delete_part, name='delete_part'),
    
    #Customers
    path('customers/', customers_list, name='customers_list'),
    path('customers/add/', add_customer, name='add_customer'),
    path('customers/<int:customer_id>/edit/', edit_customer, name='edit_customer'),
    path('customers/<int:customer_id>/delete/', delete_customer, name='delete_customer'),
    path('customers/<int:customer_id>/devices/', customer_devices, name='customer_devices'),
    path('devices/<int:device_id>/', tasks_views.device_detail, name='device_detail'),

    
    
    path('finances/', finances_view, name='finances'),
    
    path('devices/<int:device_id>/qr/', tasks_views.generate_qr, name='generate_qr'),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)