# tasks/forms.py

from django import forms
from .models import Task, UsedPart, Device, RepairHistory, UsedPart, Part, Customer
from django.forms import inlineformset_factory

class TaskForm(forms.ModelForm):
    """
    Formulario para CRUD de tareas (Task).
    """
    class Meta:
        model = Task
        fields = ['title', 'description', 'important']
        widgets = {
            'title': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Write a title'}
            ),
            'description': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Write a description'}
            ),
            'important': forms.CheckboxInput(
                attrs={'class': 'form-check-input m-auto'}
            ),
        }

class DeviceForm(forms.ModelForm):
    """
    Formulario para registrar/editar dispositivos (Device).
    """
    class Meta:
        model = Device
        fields = [
            'customer', 
            'device_type', 
            'issue', 
            'comments', 
            'quote', 
            'advance_payment', 
            'status'
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'device_type': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Tipo de dispositivo'}
            ),
            'issue': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Describe el problema'}
            ),
            'comments': forms.Textarea(
                attrs={'class': 'form-control', 'placeholder': 'Comentarios adicionales'}
            ),
            'quote': forms.NumberInput(
                attrs={'class': 'form-control', 'placeholder': 'Cotización'}
            ),
            'advance_payment': forms.NumberInput(
                attrs={'class': 'form-control', 'placeholder': 'Anticipo'}
            ),
            'status': forms.Select(
                attrs={'class': 'form-control'}
            ),
        }
        
class RegisterDeviceForm(forms.Form):
    STATUS_CHOICES = [
        ('QUEUE', 'En cola de reparación'),
        ('IN_PROGRESS', 'En reparación'),
        ('READY', 'En espera de ser recogido'),
        ('DELIVERED', 'Entregado'),
        ('ABANDONED', 'Abandonado'),
    ]
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    phone = forms.CharField(
        max_length=15,
        required=True,
        label='Teléfono del cliente',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    name = forms.CharField(
        max_length=100,
        required=False,
        label='Nombre del cliente',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    device_type = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    issue = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control'})
    )
    comments = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control'})
    )
    quote = forms.DecimalField(
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    advance_payment = forms.DecimalField(
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

class UsedPartForm(forms.ModelForm):
    class Meta:
        model = UsedPart
        fields = ["part", "quantity"]
        widgets = {
            'part': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
        }

# Este formset relaciona la clase principal (RepairHistory) con la secundaria (UsedPart).
UsedPartFormSet = inlineformset_factory(
    parent_model=RepairHistory,
    model=UsedPart,
    fields=['part', 'quantity'],  # Campos que queremos editar
    extra=1,                      # Cuántos forms en blanco se mostrarán por defecto
    can_delete=True               # Permitir eliminar líneas si se quiere
)

class PartForm(forms.ModelForm):
    class Meta:
        model = Part
        fields = ['name', 'stock', 'description', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            # 'image' -> <input type="file">
        }
        
class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }