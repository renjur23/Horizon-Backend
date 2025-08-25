from django.db import models
import uuid
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from geopy.distance import geodesic
from datetime import datetime, date, timedelta
DEFAULT_LOCATION_NAME = "Default Location"
DEFAULT_COORDS = (53.3845, -6.2960) 

class Client(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client_name = models.CharField(max_length=255)
    client_contact = models.CharField(max_length=20, blank=True, null=True)
    client_email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.client_name
    
    class Meta:
        ordering = ['client_name']
        verbose_name = "Client"
        verbose_name_plural = "Clients"

class Location(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    location_name = models.CharField(max_length=255)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.location_name
    class Meta:
        ordering = ['location_name']
        verbose_name = "Location"
        verbose_name_plural = "Locations"



class InverterStatus(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inverter_status_name = models.CharField(max_length=255)

    def __str__(self):
        return self.inverter_status_name
    
    class Meta:
        ordering = ['inverter_status_name']

class Inverter(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    unit_id = models.CharField(max_length=255)
    model = models.CharField(max_length=255)
    given_name = models.CharField(max_length=255)
    given_start_name = models.CharField(max_length=255)
    serial_no = models.CharField(max_length=255)
    inverter_status = models.ForeignKey(
        InverterStatus, on_delete=models.SET_NULL, null=True, related_name="inverters"
    )
    remarks = models.TextField(blank=True, null=True)
    link_to_installation = models.CharField(
    max_length=255, blank=True, null=True,
    help_text="Enter or auto-sync VRM Installation ID")
    

    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.given_name} ({self.unit_id})"

    def save(self, *args, **kwargs):
        from order.models import Order, Location  # local import to avoid circular imports

        default_location = Location.objects.filter(location_name=DEFAULT_LOCATION_NAME).first()

        # Check if inverter is linked to any order (PO)
        has_po = Order.objects.filter(inverter_id=self).exists()

        # Auto-assign default location if no PO and location not already set
        if not has_po and not self.location and default_location:
            self.location = default_location

        # Check distance from default and send alert if too far
        if self.location and default_location and self.location != default_location:
            if self.location.latitude and self.location.longitude:
                inverter_coords = (self.location.latitude, self.location.longitude)
                distance = geodesic(DEFAULT_COORDS, inverter_coords).meters

                if distance > 200:
                    from django.core.mail import send_mail
                    send_mail(
                        subject="⚠️ Inverter Distance Alert",
                        message=f"Inverter '{self.unit_id}' is located {distance:.2f} meters from the default location.",
                        from_email="horizonoffgridenergy@gmail.com",
                        recipient_list=["renjithr.horizon.offgrid@gmail.com"],
                        fail_silently=False,
                    )

        super().save(*args, **kwargs)
        
    class Meta:
        ordering = ['unit_id']
        verbose_name = "Inverter"
        verbose_name_plural = "Inverters"



class Generator(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    generator_no = models.CharField(max_length=255)
    generator_size = models.IntegerField()
    fuel_consumption = models.IntegerField()

    def __str__(self):
        return self.generator_no


class SiteContact(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    site_contact_name = models.CharField(max_length=255)
    site_contact_email = models.EmailField()
    site_contact_number = models.CharField(max_length=20)

    def __str__(self):
        return self.site_contact_name


class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    po_number = models.CharField(max_length=255)
    contract_no = models.CharField(max_length=255)
    issued_to = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="orders", null=True, blank=True
    )
    location_id = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, related_name="orders"
    )
    start_date =models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    inverter_id = models.ForeignKey(
        Inverter, on_delete=models.SET_NULL, null=True, related_name="orders"
    )
    generator_no = models.ForeignKey(
        Generator, on_delete=models.SET_NULL, null=True, related_name="orders"
    )
    remarks = models.TextField(blank=True, null=True)
    site_contact_id = models.ForeignKey(
        SiteContact, on_delete=models.SET_NULL, null=True, related_name="orders"
    )
    fuel_price = models.FloatField(default=1.25,null=True, blank=True)
    co2_emission_per_litre = models.FloatField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    purchase_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"PO: {self.po_number} - {self.issued_to}"
    
    class Meta:
        ordering = ['-start_date']   


class InverterSimDetail(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    inverter_id = models.ForeignKey(
        Inverter, on_delete=models.CASCADE, related_name="sim_details"
    )
    serial_no = models.CharField(max_length=255)
    user_no = models.CharField(max_length=255)
    installation_date = models.DateField()
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"SIM Detail for {self.inverter_id}"


class InverterUtilizationStatus(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inverter_utilization_status_name = models.CharField(max_length=255)

    def __str__(self):
        return self.inverter_utilization_status_name


class InverterUtilization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField()
    inverter_id = models.ForeignKey(
        Inverter, on_delete=models.CASCADE, related_name="utilizations"
    )
    model = models.CharField(max_length=255)
    status = models.ForeignKey(
        InverterUtilizationStatus,
        on_delete=models.SET_NULL,
        null=True,
        related_name="utilizations",
    )

    def __str__(self):
        return f"Utilization {self.date} - {self.inverter_id}"


class ServiceStatus(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_status_name = models.CharField(max_length=255)

    def __str__(self):
        return self.service_status_name


class ServiceRecords(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_token_number = models.CharField(max_length=255)
    inverter_id = models.ForeignKey(
        Inverter, on_delete=models.CASCADE, related_name="service_records"
    )
    date_of_service = models.DateField()
    problem = models.TextField()
    repair_done = models.CharField(max_length=255)
    status = models.ForeignKey(
        ServiceStatus,
        on_delete=models.SET_NULL,
        null=True,
        related_name="service_records",
    )
    distance_travelled = models.CharField(max_length=255)
    hours_spent_on_travel = models.CharField(max_length=255)
    warranty_claim = models.CharField(max_length=255)
    hours_spent_on_site = models.CharField(max_length=255)
    base = models.CharField(max_length=255)
    service_location = models.CharField(max_length=255)

    def __str__(self):
        return f"Service {self.service_token_number} for {self.inverter_id}"



class Usage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inverter_id = models.ForeignKey(
        Inverter, on_delete=models.CASCADE, related_name="usages"
    )
    order_id = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="usages",null=True,
    blank=True)
    is_yard = models.BooleanField(default=False) 
    date = models.DateField()
    kw_consumed = models.FloatField()
    generator_run_hour = models.FloatField()
    inverter_usage_calculated = models.CharField(max_length=255)
    site_run_hour = models.FloatField(default=24)
    generator_run_hour_save = models.CharField(max_length=255)
    inverter_usage_based_on_site_run_hour = models.CharField(max_length=255)
    inverter_usage_based_on_site = models.CharField(max_length=255)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)
    
    
    class Meta:
        unique_together = ('inverter_id', 'order_id', 'date')

    def __str__(self):
        return f"Usage {self.date} - {self.inverter_id}"
    
    class Meta:
        unique_together = ('inverter_id', 'order_id', 'date')
        ordering = ['-date']
        verbose_name = "Usage Record"
        verbose_name_plural = "Usage Records"
        
STATUS_CHOICES =  [('OK', 'OK'),
        ('NOT_OK', 'Not OK'),
        ('NA', 'Not Applicable'),]

UNIT_STATUS_CHOICES = [
    ('Ready for Hire', 'Ready for Hire'),
    ('Under Maintenance', 'Under Maintenance'),
]

class Checklist(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    unit_no = models.CharField(max_length=100)
    unit_model = models.CharField(max_length=100)
    test_time_start = models.TimeField(null=True, blank=True)
    test_time_end = models.TimeField(null=True, blank=True)
    test_time = models.DurationField(null=True, blank=True) 
    load = models.CharField(max_length=100, blank=True)
    battery_voltage_start = models.CharField(max_length=20, blank=True)
    battery_voltage_end = models.CharField(max_length=20, blank=True)
    voltage_dip = models.CharField(max_length=20, blank=True)
    unit_status = models.CharField(max_length=20, choices=UNIT_STATUS_CHOICES)
    tested_by = models.CharField(max_length=100)
    date = models.DateField()


    def save(self, *args, **kwargs):
        if self.test_time_start and self.test_time_end:
            start_dt = datetime.combine(date.today(), self.test_time_start)
            end_dt = datetime.combine(date.today(), self.test_time_end)

            # Handle wrap-around (e.g., end time is past midnight)
            if end_dt < start_dt:
                end_dt += timedelta(days=1)

            self.test_time = end_dt - start_dt

        super().save(*args, **kwargs)

    def _str_(self):
        return f"{self.unit_no} - {self.unit_model}"

class ChecklistItem(models.Model):
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, related_name='items')
    section = models.CharField(max_length=100) 
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    remarks = models.TextField(blank=True,null=True)

class BatteryVoltage(models.Model):
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, related_name='batteries')
    battery_number = models.PositiveIntegerField()
    voltage = models.CharField(max_length=20, blank=True)