# tasks/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.db import IntegrityError
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Device, Customer
from .forms import RegisterDeviceForm, PartForm, CustomerForm
from django.forms import inlineformset_factory
from django.contrib.auth.decorators import user_passes_test
import datetime
from django.shortcuts import render, redirect
from django.db.models import Sum
from .models import RepairHistory, Expense, FundBalance
import qrcode
from io import BytesIO
from django.http import HttpResponse
from django.db.models import Sum
from .models import Expense, FundBalance, RepairHistory
from django.db.models import Sum
from django.contrib import messages
from django.utils import timezone
import datetime


# Importa tus modelos
from .models import Task, RepairHistory, UsedPart, Part, Device, Customer

# Para formularios "rápidos" dentro de views.py (normalmente se usan en forms.py)
from django import forms

# -----------------------------------------------------
# Formularios
# -----------------------------------------------------

# Form para crear/editar Tareas
class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'important']

# Form para registrar/editar Dispositivos
class DeviceForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = [
            'customer',
            'device_type',
            'issue',
            'comments',
            'quote',
            'advance_payment',
            'status'  # Si deseas permitir elegir el estado manualmente
        ]

# Form para registrar partes usadas
class UsedPartForm(forms.ModelForm):
    class Meta:
        model = UsedPart
        fields = ['part', 'quantity']


# -----------------------------------------------------
# Vistas de Home, Signup, Signin, Logout
# -----------------------------------------------------
def home(request):
    return render(request, 'home.html')


def signup(request):
    if request.method == 'GET':
        return render(request, 'signup.html', {
            'form': UserCreationForm
        })
    else:
        if request.POST['password1'] == request.POST['password2']:
            try:
                user = User.objects.create_user(
                    username=request.POST['username'],
                    password=request.POST['password1']
                )
                user.save()
                login(request, user)
                return redirect('tasks')
            except IntegrityError:
                return render(request, 'signup.html', {
                    'form': UserCreationForm,
                    'error': 'Username already exists'
                })
        else:
            return render(request, 'signup.html', {
                'form': UserCreationForm,
                'error': 'Passwords do not match'
            })


def signin(request):
    if request.method == 'GET':
        return render(request, 'signin.html', {'form': AuthenticationForm()})
    else:
        user = authenticate(
            request,
            username=request.POST['username'],
            password=request.POST['password']
        )
        if user is None:
            return render(request, 'signin.html', {
                'form': AuthenticationForm(),
                'error': 'Username or password is incorrect'
            })
        else:
            login(request, user)
            return redirect('devices_home')  # Redirige a la home de dispositivos


@login_required
def signout(request):
    logout(request)
    return redirect('home')


# -----------------------------------------------------
# Vistas para Tasks (Tareas)
# -----------------------------------------------------
@login_required
def tasks(request):
    tasks = Task.objects.filter(user=request.user, datecompleted__isnull=True)
    return render(request, 'tasks.html', {'tasks': tasks})

@login_required
def tasks_completed(request):
    tasks = Task.objects.filter(
        user=request.user,
        datecompleted__isnull=False
    ).order_by('-datecompleted')
    return render(request, 'tasks.html', {'tasks': tasks})

@login_required
def create_tasks(request):
    if request.method == 'GET':
        return render(request, 'create_tasks.html', {'form': TaskForm()})
    else:
        try:
            form = TaskForm(request.POST)
            new_task = form.save(commit=False)
            new_task.user = request.user
            new_task.save()
            return redirect('tasks')
        except ValueError:
            return render(request, 'create_tasks.html', {
                'form': TaskForm(),
                'error': 'Please provide valid data'
            })

@login_required
def task_detail(request, task_id):
    task = get_object_or_404(Task, pk=task_id, user=request.user)
    if request.method == 'GET':
        form = TaskForm(instance=task)
        return render(request, 'task_detail.html', {'task': task, 'form': form})
    else:
        try:
            form = TaskForm(request.POST, instance=task)
            form.save()
            return redirect('tasks')
        except ValueError:
            return render(request, 'task_detail.html', {
                'task': task,
                'form': form,
                'error': "Error updating task"
            })

@login_required
def complete_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id, user=request.user)
    if request.method == 'POST':
        task.datecompleted = timezone.now()
        task.save()
        return redirect('tasks')

@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id, user=request.user)
    if request.method == 'POST':
        task.delete()
        return redirect('tasks')

def tasks_home(request):
    return render(request, "tasks_home.html")

# -----------------------------------------------------
# Vistas para Dispositivos
# -----------------------------------------------------
@login_required
def devices_home(request):
    """
    Vista principal para administrar dispositivos:
    - Registrar dispositivo
    - Ver cola de reparación
    - Dispositivos en progreso
    - Dispositivos listos
    - Dispositivos entregados
    """
    return render(request, "devices_home.html")

@login_required
def repair_queue(request):
    """
    Muestra todos los dispositivos que están en cola de reparación (status='QUEUE').
    """
    devices_in_queue = Device.objects.filter(status='QUEUE')
    return render(request, "repair_queue.html", {
        "Dispositivos en la cola de reparación": devices_in_queue
    })
    
@login_required
def device_detail(request, device_id):
    """
    Muestra la info del dispositivo, maneja el cambio de estado a través de flow_info,
    e integra el modal para registrar el pago final al pasar de READY a DELIVERED.
    """
    device = get_object_or_404(Device, pk=device_id)

    # Obtenemos el RepairHistory (siempre el mismo para este device)
    repair_history = RepairHistory.objects.filter(device=device).first()

    # Calculamos total_cost y total_to_pay
    total_cost = None
    total_to_pay = None
    if repair_history:
        total_cost = repair_history.total_cost
        total_to_pay = total_cost - device.advance_payment

    # Diccionario para manejar el "siguiente" estado
    next_state_map = {
        'QUEUE': {
            'next_state': 'IN_PROGRESS',
            'btn_text': 'Empezar a reparar'
        },
        'IN_PROGRESS': {
            'next_state': 'READY',
            'btn_text': 'Listo'
        },
        'READY': {
            'next_state': 'DELIVERED',
            'btn_text': 'Entregar'
        },
        'DELIVERED': {
            'next_state': None,
            'btn_text': 'Entregado'
        },
        'ABANDONED': {
            'next_state': None,
            'btn_text': 'Abandonado'
        }
    }

    if request.method == 'POST':
        # CASO 1: Viene del modal "deliver" (READY -> DELIVERED)
        if 'deliver' in request.POST:
            final_payment_amount_str = request.POST.get('final_payment_amount', '0')
            payment_method = request.POST.get('payment_method', '')

            try:
                final_payment_amount = float(final_payment_amount_str)
            except ValueError:
                final_payment_amount = 0.0

            # Guardar en RepairHistory
            if repair_history:
                repair_history.final_payment_amount = final_payment_amount
                repair_history.payment_method = payment_method
                repair_history.delivery_date = timezone.now()
                repair_history.save()

            # Cambiar estado a DELIVERED
            device.status = 'DELIVERED'
            device.save()
            return redirect('device_detail', device_id=device.id)

        # CASO 2: Botón normal (ej.: QUEUE->IN_PROGRESS o IN_PROGRESS->READY, etc.)
        else:
            info = next_state_map.get(device.status)
            if info and info['next_state']:
                # Interceptar si el estado actual es IN_PROGRESS -> redirigir a /complete_repair/
                if device.status == 'IN_PROGRESS':
                    return redirect('complete_repair', device_id=device.id)
                
                # De lo contrario, cambiamos de estado
                device.status = info['next_state']
                device.save()
            return redirect('device_detail', device_id=device.id)

    # GET: mostramos la página normal
    flow_info = next_state_map.get(device.status)

    # Generamos la URL del QR dinámicamente
    qr_url = f"/devices/{device_id}/qr/"

    context = {
        'device': device,
        'repair_history': repair_history,
        'total_cost': total_cost,
        'total_to_pay': total_to_pay,
        'flow_info': flow_info,
        'qr_url': qr_url,  # Añadimos el enlace del QR al contexto
    }
    return render(request, 'device_detail.html', context)

@login_required
def edit_device(request, device_id):
    """
    Edita un 'Device' y, a la vez, permite cambiar 'phone' y 'name' del cliente.
    Usa el mismo 'RegisterDeviceForm' que se usa en register_device().
    """
    device = get_object_or_404(Device, pk=device_id)
    customer = device.customer  # Relación actual con el cliente

    if request.method == 'POST':
        form = RegisterDeviceForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            name = form.cleaned_data['name']
            device_type = form.cleaned_data['device_type']
            issue = form.cleaned_data['issue']
            comments = form.cleaned_data['comments']
            quote = form.cleaned_data['quote']
            advance_payment = form.cleaned_data['advance_payment']
            status = form.cleaned_data['status']

            # Buscar o crear el cliente con el nuevo teléfono
            try:
                new_customer = Customer.objects.get(phone=phone)
                # Actualizarle el nombre si cambió
                new_customer.name = name
                new_customer.save()
            except Customer.DoesNotExist:
                # Si no existe, creamos uno nuevo
                new_customer = Customer.objects.create(
                    phone=phone,
                    name=name
                )

            # Actualizar el 'Device' con los datos del form
            device.customer = new_customer
            device.device_type = device_type
            device.issue = issue
            device.comments = comments
            device.quote = quote
            device.advance_payment = advance_payment
            device.status = status
            device.save()

            # Redirigir al detalle para ver cambios
            return redirect('device_detail', device_id=device.id)
        else:
            # Si el form no es válido, se vuelve a mostrar con errores
            return render(request, 'edit_device.html', {
                'form': form,
                'device': device
            })
    else:
        # GET: Mostrar el formulario con datos actuales de Device y Customer
        initial_data = {
            'phone': customer.phone if customer else '',
            'name': customer.name if customer else '',
            'device_type': device.device_type,
            'issue': device.issue,
            'comments': device.comments,
            'quote': device.quote,
            'advance_payment': device.advance_payment,
            'status': device.status,
        }
        form = RegisterDeviceForm(initial=initial_data)

    return render(request, 'edit_device.html', {
        'form': form,
        'device': device
    })

def public_device_detail(request, device_id):
    """
    Vista pública accesible sin login.
    Muestra la información básica del dispositivo y su estatus en grande.
    """
    device = get_object_or_404(Device, pk=device_id)
    repair_history = RepairHistory.objects.filter(device=device).first()

    context = {
        'device': device,
        'repair_history': repair_history,
    }
    return render(request, 'public_device_detail.html', context)

@login_required
def repair_queue(request):
    """
    Muestra todos los dispositivos que están en cola de reparación (QUEUE).
    """
    devices_in_queue = Device.objects.filter(status='QUEUE')
    return render(request, "repair_queue.html", {
        "devices_in_queue": devices_in_queue
    })

@login_required
def devices_in_progress(request):
    """
    Muestra todos los dispositivos en estado IN_PROGRESS.
    """
    devices_in_progress = Device.objects.filter(status='IN_PROGRESS')
    return render(request, "devices_in_progress.html", {
        "devices_in_progress": devices_in_progress
    })

@login_required
def devices_ready(request):
    """
    Muestra todos los dispositivos en estado READY (listos para recoger).
    """
    devices_ready = Device.objects.filter(status='READY')
    return render(request, "devices_ready.html", {
        "devices_ready": devices_ready
    })

@login_required
def devices_delivered(request):
    """
    Muestra todos los dispositivos en estado DELIVERED (entregados).
    """
    devices_delivered = Device.objects.filter(status='DELIVERED')
    return render(request, "devices_delivered.html", {
        "devices_delivered": devices_delivered
    })
def check_phone(request):
    """
    Busca si el número de teléfono existe en la tabla Customer
    y retorna un JSON con {'exists': True/False, 'name': '...'}
    """
    phone = request.GET.get('phone', None)
    if phone:
        try:
            customer = Customer.objects.get(phone=phone)
            return JsonResponse({
                'exists': True,
                'name': customer.name
            })
        except Customer.DoesNotExist:
            return JsonResponse({'exists': False})
    else:
        return JsonResponse({'exists': False})

@login_required
def register_device(request):
    if request.method == 'POST':
        form = RegisterDeviceForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            name = form.cleaned_data['name']
            device_type = form.cleaned_data['device_type']
            issue = form.cleaned_data['issue']
            comments = form.cleaned_data['comments']
            quote = form.cleaned_data['quote']
            advance_payment = form.cleaned_data['advance_payment']
            status = form.cleaned_data['status']

            # Buscar/crear Customer
            try:
                customer = Customer.objects.get(phone=phone)
            except Customer.DoesNotExist:
                customer = Customer.objects.create(
                    phone=phone,
                    name=name or 'Unnamed Customer'
                )

            # Crear el Device
            new_device = Device.objects.create(
                customer=customer,
                device_type=device_type,
                issue=issue,
                comments=comments,
                quote=quote,
                advance_payment=advance_payment,
                status=status  # respeta el valor del formulario
            )

            # REDIRECCIÓN: ahora que se creó, nos vamos al detalle
            return redirect('device_detail', device_id=new_device.id)
    else:
        form = RegisterDeviceForm()

    return render(request, 'register_device.html', {'form': form})


@login_required
def complete_repair(request, device_id):
    """
    Vista que permite finalizar la reparación de un dispositivo IN_PROGRESS,
    registrando las refacciones usadas y el costo final. Si el dispositivo
    ya está en READY, simplemente muestra el resumen con las partes usadas.
    """
    device = get_object_or_404(Device, pk=device_id)
    
    # Obtenemos o creamos el RepairHistory para este Device
    repair_history, _ = RepairHistory.objects.get_or_create(device=device)
    
    # Si el dispositivo ya está en READY, mostramos el resumen
    if device.status == 'READY':
        used_parts = repair_history.used_parts.all()
        total_cost = repair_history.total_cost
        total_to_pay = total_cost - device.advance_payment
        return render(request, 'complete_repair_summary.html', {
            'device': device,
            'used_parts': used_parts,
            'total_cost': total_cost,
            'total_to_pay': total_to_pay
        })

    # Asumimos que el dispositivo está en IN_PROGRESS;
    # si está en otro estado, podríamos redirigir o manejarlo de otra forma
    if request.method == 'POST':
        # 1) Leer el costo final
        final_cost_str = request.POST.get('final_cost', '0')
        try:
            final_cost = float(final_cost_str)
        except ValueError:
            final_cost = 0.0

        # 2) Recorrer todas las refacciones y crear UsedPart para las que tengan cantidad > 0
        parts = Part.objects.all()
        for part in parts:
            field_name = f"quantity_{part.id}"
            quantity_str = request.POST.get(field_name, '0')
            try:
                quantity = int(quantity_str)
            except ValueError:
                quantity = 0
            
            if quantity > 0:
                used_part = UsedPart(repair=repair_history, part=part, quantity=quantity)
                try:
                    used_part.save()  # Descuenta stock si está disponible
                except ValueError as e:
                    # Si no hay stock suficiente, regresamos al formulario mostrando el error
                    return render(request, 'complete_repair.html', {
                        'device': device,
                        'parts': parts,
                        'error': str(e)
                    })

        # 3) Guardar el costo final en RepairHistory
        repair_history.total_cost = final_cost
        repair_history.completion_date = timezone.now()  # Opcional (fecha de finalización)
        repair_history.save()

        # 4) Cambiar estado del dispositivo a READY
        device.status = 'READY'
        device.save()

        # 5) Redirigir a esta misma vista para mostrar el resumen
        return redirect('complete_repair', device_id=device.id)
    
    else:
        # GET: Mostrar el formulario para registrar refacciones usadas
        parts = Part.objects.all()
        return render(request, 'complete_repair.html', {
            'device': device,
            'parts': parts,
        })
    
# -----------------------------------------------------
# Vistas para las Partes Usadas (UsedPart)
# -----------------------------------------------------
@login_required
def add_used_parts(request, repair_id):
    repair = get_object_or_404(RepairHistory, pk=repair_id)
    if request.method == "POST":
        form = UsedPartForm(request.POST)
        if form.is_valid():
            try:
                used_part = form.save(commit=False)
                used_part.repair = repair
                # Guardar la parte usada y actualizar el stock
                used_part.save()
                return redirect("repair_detail", repair_id=repair_id) 
                # Asegúrate de tener definida la URL y la vista "repair_detail"
            except ValueError as e:
                # Maneja el error de stock insuficiente
                form.add_error("quantity", str(e))
    else:
        form = UsedPartForm()
    return render(request, "add_used_parts.html", {
        "form": form,
        "repair": repair
    })

# Verificar que sea superuser
def superuser_required(user):
    return user.is_superuser

@user_passes_test(superuser_required)
def parts_list(request):
    query = request.GET.get('q')  # Lo que se escriba en la barra de búsqueda
    if query:
        parts = Part.objects.filter(name__icontains=query)
    else:
        parts = Part.objects.all()

    return render(request, 'parts_list.html', {
        'parts': parts
    })
    
@user_passes_test(superuser_required)
def add_part(request):
    if request.method == 'POST':
        form = PartForm(request.POST, request.FILES)  # Incluye request.FILES para subir imagen
        if form.is_valid():
            form.save()
            return redirect('parts_list')
    else:
        form = PartForm()
    return render(request, 'part_form.html', {'form': form, 'title': 'Add Part'})

@user_passes_test(superuser_required)
def edit_part(request, part_id):
    part = get_object_or_404(Part, pk=part_id)
    if request.method == 'POST':
        form = PartForm(request.POST, request.FILES, instance=part)
        if form.is_valid():
            form.save()
            return redirect('parts_list')
    else:
        form = PartForm(instance=part)
    return render(request, 'part_form.html', {'form': form, 'title': 'Edit Part'})

@user_passes_test(superuser_required)
def delete_part(request, part_id):
    part = get_object_or_404(Part, pk=part_id)
    if request.method == 'POST':
        part.delete()
        return redirect('parts_list')
    # Si deseas una página de confirmación
    return render(request, 'confirm_delete_part.html', {'part': part})


# -----------------------------------------------------
# Vistas para los clientes
# -----------------------------------------------------

@user_passes_test(superuser_required)
def customers_list(request):
    customers = Customer.objects.all()
    return render(request, 'customers_list.html', {'customers': customers})

@user_passes_test(superuser_required)
def add_customer(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('customers_list')
    else:
        form = CustomerForm()
    return render(request, 'customer_form.html', {'form': form, 'title': 'Agregar Cliente'})

@user_passes_test(superuser_required)
def edit_customer(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect('customers_list')
    else:
        form = CustomerForm(instance=customer)
    return render(request, 'customer_form.html', {'form': form, 'title': 'Editar Cliente'})

@user_passes_test(superuser_required)
def delete_customer(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    if request.method == 'POST':
        customer.delete()
        return redirect('customers_list')
    return render(request, 'confirm_delete_customer.html', {'customer': customer})

@user_passes_test(superuser_required)
def customer_devices(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    devices = Device.objects.filter(customer=customer)

    return render(request, 'customer_devices.html', {
        'customer': customer,
        'devices': devices
    })

# -----------------------------------------------------
# Ejemplo de vista para detalle de la reparación 
# -----------------------------------------------------
@login_required
def repair_detail(request, repair_id):
    """
    Ejemplo de vista para ver el detalle de una reparación en RepairHistory,
    incluyendo las partes usadas.
    """
    repair = get_object_or_404(RepairHistory, pk=repair_id)
    used_parts = repair.used_parts.all()
    return render(request, 'repair_detail.html', {
        "repair": repair,
        "used_parts": used_parts
    })
    
# Importa los modelos que EXISTEN en tu models.py
from .models import RepairHistory, Expense, FundBalance, Device

def finances_view(request):
    """
    Módulo de finanzas que muestra:
      - Ingresos (de RepairHistory) = final_payment_amount
      - Gastos (de Expense)
      - Fondos iniciales (de FundBalance)
      - Formularios para crear/editar gasto
      - Botón de reset
    """
    # 1) Obtener o crear un único registro de fondos (FundBalance)
    fund, created = FundBalance.objects.get_or_create(id=1)

    # ---------------------------
    # Manejar formularios POST
    # ---------------------------
    if request.method == 'POST':
        # A) Actualizar fondos iniciales
        if 'update_funds' in request.POST:
            cash = request.POST.get('initial_cash', '0')
            card = request.POST.get('initial_card', '0')
            try:
                fund.initial_cash_fund = float(cash)
                fund.initial_card_fund = float(card)
                fund.save()
                messages.success(request, "Fondos iniciales actualizados correctamente.")
            except ValueError:
                messages.error(request, "Error al actualizar fondos: revisa los valores numéricos.")

            return redirect('finances')

        # B) Agregar un gasto
        elif 'add_expense' in request.POST:
            name = request.POST.get('name', '')
            date_str = request.POST.get('date', '')  # formato 'YYYY-MM-DD'
            cash_spent = request.POST.get('cash_spent', '0')
            card_spent = request.POST.get('card_spent', '0')

            try:
                date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                date_obj = datetime.date.today()  # Si hay error, usar fecha de hoy

            Expense.objects.create(
                name=name,
                date=date_obj,
                cash_spent=float(cash_spent or 0),
                card_spent=float(card_spent or 0),
            )
            messages.success(request, "Gasto agregado correctamente.")
            return redirect('finances')

        # C) Editar un gasto (vía modal)
        elif 'edit_expense' in request.POST:
            expense_id = request.POST.get('expense_id')
            expense = get_object_or_404(Expense, pk=expense_id)

            name = request.POST.get('name', '')
            date_str = request.POST.get('date', '')
            cash_spent = request.POST.get('cash_spent', '0')
            card_spent = request.POST.get('card_spent', '0')

            # Parse fecha
            try:
                date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                date_obj = expense.date  # Dejar la anterior si hay error

            # Actualizar
            expense.name = name
            expense.date = date_obj
            expense.cash_spent = float(cash_spent or 0)
            expense.card_spent = float(card_spent or 0)
            expense.save()

            messages.success(request, "Gasto editado correctamente.")
            return redirect('finances')

        # D) Resetear finanzas
        elif 'reset_finances' in request.POST:
            # 1. Calcular lo acumulado
            incomes_cash = RepairHistory.objects.filter(payment_method='CASH').aggregate(
                total=Sum('final_payment_amount')
            )['total'] or 0
            incomes_card = RepairHistory.objects.filter(payment_method='CARD').aggregate(
                total=Sum('final_payment_amount')
            )['total'] or 0

            expenses_cash = Expense.objects.aggregate(Sum('cash_spent'))['cash_spent__sum'] or 0
            expenses_card = Expense.objects.aggregate(Sum('card_spent'))['card_spent__sum'] or 0

            # 2. Nuevo fondo inicial = fondo_inicial + (ingresos - gastos)
            final_cash = fund.initial_cash_fund + incomes_cash - expenses_cash
            final_card = fund.initial_card_fund + incomes_card - expenses_card

            fund.initial_cash_fund = final_cash
            fund.initial_card_fund = final_card
            fund.save()

            # 3. Reiniciar RepairHistory (borrar o poner a 0) 
            #    Para no perder datos de devices, puedes poner final_payment_amount=0
            #    o si prefieres, .delete() para eliminar esos historiales.
            for rh in RepairHistory.objects.all():
                rh.final_payment_amount = 0
                rh.payment_method = None
                rh.delivery_date = None
                rh.save()

            # 4. Borrar gastos
            Expense.objects.all().delete()

            messages.success(request, "Finanzas reseteadas. Fondos iniciales ajustados con las ganancias.")
            return redirect('finances')

    # ---------------------------
    # GET: Mostrar datos
    # ---------------------------
    # 1) Ingresos => de RepairHistory con final_payment_amount > 0
    incomes_qs = RepairHistory.objects.filter(final_payment_amount__gt=0).select_related('device')
    # Para filtrar solo ENTREGADOS, podrías añadir .filter(device__status='DELIVERED') si deseas

    # 2) Gastos => de Expense
    expenses_qs = Expense.objects.all().order_by('-date')

    # 3) Calcular totales
    incomes_cash = incomes_qs.filter(payment_method='CASH').aggregate(Sum('final_payment_amount'))['final_payment_amount__sum'] or 0
    incomes_card = incomes_qs.filter(payment_method='CARD').aggregate(Sum('final_payment_amount'))['final_payment_amount__sum'] or 0
    expenses_cash = expenses_qs.aggregate(Sum('cash_spent'))['cash_spent__sum'] or 0
    expenses_card = expenses_qs.aggregate(Sum('card_spent'))['card_spent__sum'] or 0

    current_cash = fund.initial_cash_fund + incomes_cash - expenses_cash
    current_card = fund.initial_card_fund + incomes_card - expenses_card
    total_balance = current_cash + current_card

    context = {
        'fund': fund,  # Fondos iniciales
        'incomes': incomes_qs,
        'expenses': expenses_qs,

        'incomes_cash': incomes_cash,
        'incomes_card': incomes_card,
        'expenses_cash': expenses_cash,
        'expenses_card': expenses_card,

        'current_cash': current_cash,
        'current_card': current_card,
        'total_balance': total_balance,
    }
    return render(request, 'finances.html', context)

def generate_qr(request, device_id):
    """
    Genera un código QR con un enlace a la vista pública del dispositivo.
    """
    # Construye la URL pública en lugar de la de 'device_detail'
    url = request.build_absolute_uri(f"/public/{device_id}/")

    # Genera el QR
    qr = qrcode.make(url)
    buffer = BytesIO()
    qr.save(buffer)
    buffer.seek(0)

    # Retorna la imagen PNG
    return HttpResponse(buffer.getvalue(), content_type="image/png")