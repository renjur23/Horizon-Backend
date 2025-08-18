# # ponumbers/admin.py
from django.utils.html import format_html
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import *

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'client_contact', 'client_email')
    search_fields = ('client_name', 'client_contact', 'client_email')
    
    
@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('location_name', 'latitude', 'longitude')
    search_fields = ('location_name',)

@admin.register(InverterStatus)
class InverterStatusAdmin(admin.ModelAdmin):
    list_display = ('inverter_status_name',)
    search_fields = ('inverter_status_name',)

@admin.register(Inverter)
class InverterAdmin(admin.ModelAdmin):
    list_display = ('unit_id', 'model', 'given_name', 'inverter_status')
    list_filter = ('inverter_status',)
    search_fields = ('unit_id', 'model', 'given_name', 'serial_no')
    raw_id_fields = ('inverter_status',)

@admin.register(Generator)
class GeneratorAdmin(admin.ModelAdmin):
    list_display = ('generator_no', 'generator_size', 'fuel_consumption')
    search_fields = ('generator_no',)

@admin.register(SiteContact)
class SiteContactAdmin(admin.ModelAdmin):
    list_display = ('site_contact_name', 'site_contact_email', 'site_contact_number')
    search_fields = ('site_contact_name', 'site_contact_email')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id','po_number', 'contract_no', 'issued_to', 'start_date', 'end_date')
    list_filter = ('issued_to', 'location_id')
    search_fields = ('po_number', 'contract_no')
    raw_id_fields = ('issued_to', 'location_id', 'inverter_id', 'generator_no', 'site_contact_id')
    date_hierarchy = 'start_date'

@admin.register(InverterSimDetail)
class InverterSimDetailAdmin(admin.ModelAdmin):
    list_display = ( 'inverter_id', 'installation_date')
    search_fields = ( 'serial_no', 'user_no')
    raw_id_fields = ('inverter_id',)
    date_hierarchy = 'installation_date'

@admin.register(InverterUtilizationStatus)
class InverterUtilizationStatusAdmin(admin.ModelAdmin):
    list_display = ('inverter_utilization_status_name',)
    search_fields = ('inverter_utilization_status_name',)

@admin.register(InverterUtilization)
class InverterUtilizationAdmin(admin.ModelAdmin):
    list_display = ('date', 'inverter_id', 'status')
    list_filter = ('status',)
    search_fields = ('inverter_id__unit_id', 'inverter_id__given_name')
    raw_id_fields = ('inverter_id', 'status')
    date_hierarchy = 'date'

@admin.register(ServiceStatus)
class ServiceStatusAdmin(admin.ModelAdmin):
    list_display = ('service_status_name',)
    search_fields = ('service_status_name',)

@admin.register(ServiceRecords)
class ServiceRecordsAdmin(admin.ModelAdmin):
    list_display = ('service_token_number', 'inverter_id', 'date_of_service', 'status')
    list_filter = ('status',)
    search_fields = ('service_token_number', 'inverter_id__unit_id')
    raw_id_fields = ('inverter_id', 'status')
    date_hierarchy = 'date_of_service'


@admin.register(Usage)
class UsageAdmin(admin.ModelAdmin):
    list_display = ('date', 'inverter_id', 'order_id')
    search_fields = ('inverter_id__unit_id', 'order_id__po_number')
    raw_id_fields = ('inverter_id', 'order_id')
    date_hierarchy = 'date'

class ChecklistItemInline(admin.TabularInline):
    model = ChecklistItem
    extra = 0

class BatteryVoltageInline(admin.TabularInline):
    model = BatteryVoltage
    extra = 0

@admin.register(Checklist)
class ChecklistAdmin(admin.ModelAdmin):
    list_display = ('unit_no', 'unit_model', 'tested_by', 'unit_status', 'date','test_time')
    search_fields = ('unit_no', 'unit_model', 'tested_by')
    list_filter = ('unit_status', 'date')
    date_hierarchy = 'date' 
    inlines = [ChecklistItemInline, BatteryVoltageInline]
    readonly_fields = ('date','test_time')

# Optional: Registering other models separately (if needed)
@admin.register(ChecklistItem)
class ChecklistItemAdmin(admin.ModelAdmin):
    list_display = ('checklist', 'section', 'description', 'status')

@admin.register(BatteryVoltage)
class BatteryVoltageAdmin(admin.ModelAdmin):
    list_display = ('checklist', 'battery_number', 'voltage')