# tasks/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

# -----------------------------------------------------
# Modelo para las Tareas (Task)
# -----------------------------------------------------
class Task(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    datecompleted = models.DateTimeField(null=True, blank=True)
    important = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Relaciona la tarea con un usuario

    def __str__(self):
        return f"{self.title} - by {self.user.username}"


# -----------------------------------------------------
# Modelo para los Clientes (Customer)
# -----------------------------------------------------
class Customer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    phone = models.CharField(max_length=15, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.phone})"


# -----------------------------------------------------
# Modelo para los Dispositivos (Device)
# -----------------------------------------------------
class Device(models.Model):
    STATUS_CHOICES = [
        ('QUEUE', 'En cola de reparación'),
        ('IN_PROGRESS', 'En reparación'),
        ('READY', 'En espera de ser recogido'),
        ('DELIVERED', 'Entregado'),
        ('ABANDONED', 'Abandonado'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='QUEUE')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)  # Relación con el cliente
    device_type = models.CharField(max_length=50)  # Ej. consola, control, smartphone, etc.
    issue = models.TextField()  # Descripción del fallo
    comments = models.TextField(blank=True, null=True)  # Comentarios adicionales
    quote = models.DecimalField(max_digits=10, decimal_places=2)  # Cotización
    advance_payment = models.DecimalField(max_digits=10, decimal_places=2)  # Anticipo
    created_at = models.DateTimeField(default=now)       # Fecha de registro
    updated_at = models.DateTimeField(auto_now=True)     # Fecha de última actualización

    def __str__(self):
        return f"{self.device_type} ({self.customer.name})"


# -----------------------------------------------------
# Modelo para Historial de Reparaciones (RepairHistory)
# Se usa para representar ingresos cuando se entrega el dispositivo.
# -----------------------------------------------------
class RepairHistory(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    completion_date = models.DateTimeField(blank=True, null=True)
    delivery_date = models.DateTimeField(blank=True, null=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    final_payment_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    PAYMENT_CHOICES = [
        ('CASH', 'Efectivo'),
        ('CARD', 'Tarjeta'),
    ]
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, null=True, blank=True)

    # Campo nuevo para el folio
    folio = models.CharField(max_length=20, unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        """
        Cada vez que se crea un RepairHistory por primera vez,
        se guarda, y luego usamos su 'id' para generar un folio único.
        """
        # 1. Llamamos al save normal (para asegurarnos de tener un self.id)
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # 2. Si es nuevo y no tiene folio, lo generamos usando su id
        if is_new and not self.folio:
            self.folio = f"R-{self.id:05d}"  # Ejemplo: R-00001
            # Guardamos de nuevo, pero solo actualizamos 'folio'
            super().save(update_fields=['folio'])

    def __str__(self):
        return f"Historial {self.folio or self.id} de {self.device}"


# -----------------------------------------------------
# Modelo para las Partes o Refacciones (Part)
# -----------------------------------------------------
class Part(models.Model):
    name = models.CharField(max_length=100)
    stock = models.PositiveIntegerField()
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='parts_images/', null=True, blank=True)

    def __str__(self):
        return f"{self.name} - Stock: {self.stock}"


# -----------------------------------------------------
# Modelo para las Partes Usadas en una Reparación (UsedPart)
# -----------------------------------------------------
class UsedPart(models.Model):
    repair = models.ForeignKey(
        RepairHistory,
        on_delete=models.CASCADE,
        related_name="used_parts"
    )
    part = models.ForeignKey(Part, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def save(self, *args, **kwargs):
        """
        Al crear por primera vez un UsedPart, descuenta la cantidad
        utilizada del stock de la parte.
        """
        if not self.pk:  # Solo para nuevos registros
            if self.part.stock >= self.quantity:
                self.part.stock -= self.quantity
                self.part.save()
            else:
                raise ValueError(
                    f"Not enough stock for {self.part.name}. "
                    f"Available: {self.part.stock}, "
                    f"Requested: {self.quantity}"
                )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Used {self.quantity} of {self.part.name} in {self.repair}"


# -----------------------------------------------------
# Modelo para Gastos (Expense)
# -----------------------------------------------------
class Expense(models.Model):
    name = models.CharField(max_length=200)
    date = models.DateField()
    cash_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    card_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.name} ({self.date})"


# -----------------------------------------------------
# Modelo para Fondos (FundBalance)
# -----------------------------------------------------
class FundBalance(models.Model):
    """
    Maneja el fondo en efectivo y el fondo en tarjeta,
    además de fondos iniciales que se suman o restan
    al hacer 'reset' de finanzas.
    """
    effective_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    card_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    initial_cash_fund = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    initial_card_fund = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return (f"FundBalance -> "
                f"Efectivo: {self.effective_balance}, "
                f"Tarjeta: {self.card_balance}")
