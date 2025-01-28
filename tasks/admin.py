from django.contrib import admin
from .models import Task, Customer, Device, RepairHistory, Part, UsedPart, Expense, FundBalance


class TaskAdmin(admin.ModelAdmin):
    readonly_fields = ("created", )
# Register your models here.
admin.site.register(Task, TaskAdmin)

# Admin customization for Customer model
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "phone")  # Campos a mostrar en la lista de clientes
    search_fields = ("name", "phone")  # Campos que se pueden buscar

# Admin customization for Device model
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("device_type", "customer", "status", "created_at", "updated_at")  # Campos a mostrar
    list_filter = ("status", "created_at")  # Filtros para estado y fecha
    search_fields = ("device_type", "customer__name")  # Campos que se pueden buscar
    readonly_fields = ("created_at", "updated_at")  # Campos solo lectura

# Admin customization for RepairHistory model
class RepairHistoryAdmin(admin.ModelAdmin):
    list_display = ("device", "completion_date", "delivery_date", "total_cost")  # Campos a mostrar
    list_filter = ("completion_date", "delivery_date")  # Filtros para fechas
    search_fields = ("device__device_type", "device__customer__name")  # Campos que se pueden buscar
    
@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = ("name", "stock", "description")
    search_fields = ("name",)
    
# Admin para Expense
@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("name", "date", "cash_spent", "card_spent")
    list_filter = ("date",)  # Permitir filtrar por fecha
    search_fields = ("name",)  # Permitir buscar por nombre

# Admin para FundBalance
@admin.register(FundBalance)
class FundBalanceAdmin(admin.ModelAdmin):
    list_display = ("effective_balance", "card_balance", "initial_cash_fund", "initial_card_fund")
    readonly_fields = ("effective_balance", "card_balance")  # Evitar editar los balances calculados directamente
    

# Register your models here
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Device, DeviceAdmin)
admin.site.register(RepairHistory, RepairHistoryAdmin)

