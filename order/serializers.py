from rest_framework import serializers
from .models import (
    Order, Client, Location, Inverter, Generator, SiteContact,
    InverterStatus, InverterSimDetail, InverterUtilizationStatus,
    InverterUtilization, ServiceStatus, ServiceRecords, Usage,
    Checklist, ChecklistItem, BatteryVoltage,ChecklistImage
)
from rest_framework.exceptions import ValidationError
from datetime import timedelta
from django.utils.timezone import now
from django.db import transaction
from django.shortcuts import get_object_or_404


# Supporting (Related) Serializers

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'client_name', 'client_contact', 'client_email']


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'
        
class InverterStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = InverterStatus
        fields = ['id','inverter_status_name']
        
    def validate_status(self, value):
        # Convert name to object
        try:
            return InverterStatus.objects.get(inverter_status_name=value)
        except InverterStatus.DoesNotExist:
            raise serializers.ValidationError("Invalid inverter status.")

class InverterSerializer(serializers.ModelSerializer):
    inverter_status_input = serializers.CharField(write_only=True)  # Accepts status name during POST/PATCH
    inverter_status = InverterStatusSerializer(read_only=True)   # Displays status name in GET

    class Meta:
        model = Inverter
        fields = '__all__'

    def validate_inverter_status_input(self, value):
        try:
            return InverterStatus.objects.get(inverter_status_name=value)
        except InverterStatus.DoesNotExist:
            raise serializers.ValidationError("Invalid inverter status name.")

    def create(self, validated_data):
        status_name = validated_data.pop("inverter_status_input")
        status_obj = InverterStatus.objects.get(inverter_status_name=status_name)
        validated_data["inverter_status"] = status_obj
        return super().create(validated_data)

    def update(self, instance, validated_data):
        status_name = validated_data.pop("inverter_status_input", None)

        # If status is provided, fetch and assign it
        if status_name:
            try:
                status_obj = InverterStatus.objects.get(inverter_status_name=status_name)
                instance.inverter_status = status_obj
            except InverterStatus.DoesNotExist:
                raise serializers.ValidationError({"inverter_status_input": "Invalid inverter status name."})

        # Assign all other fields manually
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class GeneratorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Generator
        fields = ['id', 'generator_no', 'generator_size', 'fuel_consumption']


class SiteContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteContact
        fields = '__all__'


# Additional Serializers for Related Models




class InverterSimDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = InverterSimDetail
        fields = '__all__'


class InverterUtilizationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = InverterUtilizationStatus
        fields = '__all__'


class InverterUtilizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = InverterUtilization
        fields = '__all__'


class ServiceStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceStatus
        fields = '__all__'


class ServiceRecordsSerializer(serializers.ModelSerializer):
    inverter_name = serializers.CharField(source='inverter_id.unit_id', read_only=True)
    status_name = serializers.CharField(source='status.service_status_name', read_only=True)

    class Meta:
        model = ServiceRecords
        fields = '__all__'

class UsageSerializer(serializers.ModelSerializer):
    inverter_given_start_name = serializers.CharField(source="inverter_id.given_start_name", read_only=True) 
    inverter_given_name = serializers.CharField(source="inverter_id.given_name", read_only=True)
    inverter_model = serializers.CharField(source="inverter_id.model", read_only=True)
    inverter_unit_id = serializers.CharField(source="inverter_id.unit_id", read_only=True)
    po_number = serializers.CharField(source="order_id.po_number", read_only=True)
    location_name = serializers.CharField(source="order_id.location_id.location_name", read_only=True)
    generator_no = serializers.CharField(source="order_id.generator_no.generator_no", read_only=True)
    
    inverter_display = serializers.SerializerMethodField()
    order_display = serializers.SerializerMethodField()

    inverter_usage_calculated = serializers.SerializerMethodField()
    generator_run_hour_save = serializers.SerializerMethodField()
    inverter_usage_based_on_site_run_hour = serializers.SerializerMethodField()
    fuel_saved = serializers.SerializerMethodField()
    fuel_cost_saved = serializers.SerializerMethodField()
    co2_saved = serializers.SerializerMethodField()

    class Meta:
        model = Usage
        fields = [
            "id", "date", "kw_consumed", "generator_run_hour", "site_run_hour",
            "inverter_usage_calculated", "generator_run_hour_save",
            "inverter_usage_based_on_site_run_hour","inverter_model",
            "inverter_given_name", "inverter_unit_id", "inverter_given_start_name",
            "po_number", "location_name", "generator_no",
            "fuel_saved", "fuel_cost_saved", "co2_saved",
            "inverter_display", "order_display",
        ]

    def get_inverter_usage_calculated(self, obj):
        return round((24 - obj.generator_run_hour) / 24, 2) if obj.generator_run_hour else 0

    def get_generator_run_hour_save(self, obj):
        return round(obj.site_run_hour - obj.generator_run_hour, 2) if obj.site_run_hour and obj.generator_run_hour else 0

    def get_inverter_usage_based_on_site_run_hour(self, obj):
        return round((obj.site_run_hour - obj.generator_run_hour) / obj.site_run_hour, 2) if obj.site_run_hour else 0

    def get_fuel_saved(self, obj):
        fuel_per_hr = obj.order_id.generator_no.fuel_consumption if obj.order_id and obj.order_id.generator_no else 6.8
        return round(self.get_generator_run_hour_save(obj) * fuel_per_hr, 2)

    def get_fuel_cost_saved(self, obj):
        fuel_price = obj.order_id.fuel_price if obj.order_id and obj.order_id.fuel_price else 1.25
        return round(self.get_fuel_saved(obj) * fuel_price, 2)

    def get_co2_saved(self, obj):
        co2_per_litre = obj.order_id.co2_emission_per_litre if obj.order_id and obj.order_id.co2_emission_per_litre else 2.68
        return round(self.get_fuel_saved(obj) * co2_per_litre, 2)
    
    def get_inverter_display(self, obj):
        """Build inverter string like: H70 10/46 ... Walls Murphystown (HZE-10/46-070)"""
        if obj.inverter_id:
            parts = [
                obj.inverter_id.given_start_name or "",
                obj.inverter_id.model or "",
                obj.inverter_id.serial_no or "",
              
            ]
            return " ".join(filter(None, parts))
        return None

    def get_order_display(self, obj):
        """Build PO string like: PO: 17888/49044 - Walls"""
        if obj.order_id:
            return f"PO: {obj.order_id.po_number}/{obj.order_id.contract_no} - {obj.order_id.issued_to.client_name}"
        return None

# Order Serializers

class OrderCreateSerializer(serializers.ModelSerializer):
    end_date = serializers.DateField(required=False, allow_null=True)
    class Meta:
        model = Order
        fields = [
            "location_id",
            "po_number",
            "issued_to",
            "contract_no",
            "inverter_id",
            "generator_no",
            "site_contact_id",
            "start_date",
             "end_date",
            "remarks",
        ]


class OrderUpdateSerializer(serializers.ModelSerializer):
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(), required=False
    )
    inverter_id = serializers.PrimaryKeyRelatedField(
        queryset=Inverter.objects.all(), required=False
    )
    generator_no = serializers.PrimaryKeyRelatedField(
        queryset=Generator.objects.all(), required=False
    )
    site_contact_id = serializers.PrimaryKeyRelatedField(
        queryset=SiteContact.objects.all(), required=False
    )
    
    fuel_price = serializers.FloatField(required=False, allow_null=True)
    co2_emission_per_litre = serializers.FloatField(required=False, allow_null=True)


    class Meta:
        model = Order
        fields = [
            "po_number",
            "contract_no",
            "location_id",
            "start_date",
            "end_date",
            "inverter_id",
            "generator_no",
            "remarks",
            "site_contact_id",
            "fuel_price",
            "co2_emission_per_litre",
        ]




class OrderSerializer(serializers.ModelSerializer):
    inverter_model = serializers.CharField(source="inverter_id.model", read_only=True)
    
    client_name = serializers.CharField(source="issued_to.client_name", read_only=True)
    
    inverter_name = serializers.SerializerMethodField()
    
    issued_to_name = serializers.CharField(
        source="issued_to.client_name", read_only=True
    )
    location_name = serializers.CharField(
        source="location_id.location_name", read_only=True
    )
  
    generator_no = serializers.CharField(
        source="generator_no.generator_no", read_only=True
    )
    site_contact_name = serializers.CharField(
        source="site_contact_id.site_contact_name", read_only=True
    )
    created_by = serializers.SerializerMethodField()

    # Write-only fields for POST/PUT using IDs
    issued_to_id = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.all(), write_only=True, source="issued_to"
    )
    location = LocationSerializer(read_only=True)
    location_id_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(),
        write_only=True,
        source="location_id",
        required=False,
    )
    inverter_id_id = serializers.PrimaryKeyRelatedField(
        queryset=Inverter.objects.all(),
        write_only=True,
        source="inverter_id",
        required=False,
    )
    generator_no_id = serializers.PrimaryKeyRelatedField(
        queryset=Generator.objects.all(),
        write_only=True,
        source="generator_no",
        required=False,
    )
    site_contact_id_id = serializers.PrimaryKeyRelatedField(
        queryset=SiteContact.objects.all(),
        write_only=True,
        source="site_contact_id",
        required=False,
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "po_number",
            "contract_no",
            "issued_to_name",
             "location", 
            "location_id",
            "inverter_name",
            "generator_no",
            "site_contact_name",
            "start_date",
            "end_date",
            "remarks",
            "fuel_price",
            "co2_emission_per_litre",
            "created_by",
            "issued_to_id",
            "location_id_id",
            "inverter_id_id",
            "generator_no_id",
            "site_contact_id_id",
            "inverter_model",
            "client_name",
            "location_name"
            
        ]
        
    def get_inverter_name(self, obj):
        if obj.inverter_id:
            parts = [
                obj.inverter_id.given_start_name or "",
                obj.inverter_id.model or "",
                obj.inverter_id.serial_no or "",
            ]
            return " ".join(filter(None, parts))  
        return None

    def get_created_by(self, obj):
        if obj.created_by:
            return obj.created_by.name
        return None

class ChecklistItemSerializer(serializers.ModelSerializer):
    checklist_id = serializers.PrimaryKeyRelatedField(
        source="checklist", queryset=Checklist.objects.all(), required=False
    )

    class Meta:
        model = ChecklistItem
        fields = ['id', 'checklist_id', 'section', 'description', 'status', 'remarks']
        read_only_fields = ['id']

    def validate_status(self, value):
        """Ensure status has only allowed values (OK, NOT_OK, NA)."""
        allowed_status = ["OK", "NOT_OK", "NA"]
        if value not in allowed_status:
            raise serializers.ValidationError(
                f"Status must be one of {allowed_status}, got '{value}'."
            )
        return value


class BatteryVoltageSerializer(serializers.ModelSerializer):
    checklist_id = serializers.PrimaryKeyRelatedField(
        source="checklist", queryset=Checklist.objects.all(), required=False
    )

    class Meta:
        model = BatteryVoltage
        fields = ['id', 'checklist_id', 'battery_number', 'voltage']
        read_only_fields = ['id']

    def validate_battery_number(self, value):
        """Battery number must be 1 → 25 only."""
        if value <= 0 or value > 25:
            raise serializers.ValidationError("Battery number must be between 1 and 25.")
        return value
    

class ChecklistImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = ChecklistImage
        fields = ["id", "image"]

    def get_image(self, obj):
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)  # full URL
        return obj.image.url if obj.image else None

class ChecklistSerializer(serializers.ModelSerializer):
    items = ChecklistItemSerializer(many=True, required=False)
    batteries = BatteryVoltageSerializer(many=True, required=False)
    images = ChecklistImageSerializer(many=True, required=False)


    # Inverter fields (FK)
    unit_no = serializers.CharField(source="inverter.unit_id", read_only=True)
    inverter_model = serializers.CharField(source="inverter.model", read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = Checklist
        fields = [
            "id",
            "inverter",
            "unit_no",
            "inverter_model",
            "status",
            "test_time_start",
            "test_time_end",
            "test_time",
            "load",
            "battery_voltage_start",
            "battery_voltage_end",
            "voltage_dip",
            "unit_status",
            "tested_by",
            "date",
            "items",
            "batteries", 
            "images"
        ]
        read_only_fields = ["unit_no", "inverter_model", "status", "test_time"]

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        batteries_data = validated_data.pop("batteries", [])
        images_data = self.context["request"].FILES.getlist("images")

        inverter = validated_data["inverter"]
        unit_status = validated_data.get("unit_status")
        with transaction.atomic():
            # 1. Create checklist
            checklist = Checklist.objects.create(**validated_data)

            # 2. Save nested items
            for item in items_data:
                ChecklistItem.objects.create(checklist=checklist, **item)

            # 3. Save nested batteries
            for battery in batteries_data:
                BatteryVoltage.objects.create(checklist=checklist, **battery)
                
                
            # 4. Save nested images
            for image_file in images_data:
                ChecklistImage.objects.create(checklist=checklist, image=image_file)

             # 5. Update inverter status based on unit_status
            if unit_status == "Operational(Ready to Hire)":
                new_status = get_object_or_404(
                    InverterStatus, inverter_status_name="Operational(Ready to Hire)"
                )
            elif unit_status == "Under Maintenance":
                new_status = get_object_or_404(
                    InverterStatus, inverter_status_name="Breakdown"
                )
            else:
                # fallback if unknown
                new_status = inverter.inverter_status  

            inverter.inverter_status = new_status
            inverter.save(update_fields=["inverter_status"])

        return checklist

    def get_status(self, obj):
        """Compute inverter status dynamically with expiry check."""
        expiry_date = obj.date + timedelta(days=30)
        if now().date() > expiry_date:
            return "Testing"
        return obj.inverter.inverter_status.inverter_status_name