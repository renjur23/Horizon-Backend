from rest_framework import serializers
from .models import (
    Order, Client, Location, Inverter, Generator, SiteContact,
    InverterStatus, InverterSimDetail, InverterUtilizationStatus,
    InverterUtilization, ServiceStatus, ServiceRecords, Usage,Checklist, ChecklistItem, BatteryVoltage
)
from rest_framework.exceptions import ValidationError



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
    inverter_usage_calculated = serializers.SerializerMethodField()
    generator_run_hour_save = serializers.SerializerMethodField()
    inverter_usage_based_on_site_run_hour = serializers.SerializerMethodField()
    inverter_usage_based_on_site = serializers.SerializerMethodField()
    inverter_given_name = serializers.CharField(source="inverter_id.given_name", read_only=True)
    inverter_unit_id = serializers.CharField(source="inverter_id.unit_id", read_only=True)
    po_number = serializers.CharField(source="order_id.po_number", read_only=True)
    location_name = serializers.CharField(source="order_id.location_id.location_name", read_only=True)
    generator_no = serializers.CharField(source="order_id.generator_no.generator_no", read_only=True)



    class Meta:
        model = Usage
        fields = [
            'id', 'inverter_id', 'order_id', 'is_yard', 'date', 'kw_consumed',
            'generator_run_hour', 'inverter_usage_calculated', 'site_run_hour',
            'generator_run_hour_save', 'inverter_usage_based_on_site_run_hour',
            'inverter_usage_based_on_site', 'created_at', 'updated_at',
            'inverter_given_name', 'inverter_unit_id','po_number',
            'location_name', 'generator_no'
        ]

 
    def get_inverter_usage_calculated(self, obj):
        try:
            return round((24 - float(obj.generator_run_hour)) / 24, 2)
        except:
            return None

    def get_generator_run_hour_save(self, obj):
        try:
            return round(float(obj.site_run_hour) - float(obj.generator_run_hour), 2)
        except:
            return None

    def get_inverter_usage_based_on_site_run_hour(self, obj):
        try:
            return round((float(obj.site_run_hour) - float(obj.generator_run_hour)) / float(obj.site_run_hour), 2)
        except:
            return None

    def get_inverter_usage_based_on_site(self, obj):
        return self.get_inverter_usage_based_on_site_run_hour(obj)

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
            return obj.created_by.email
        return None


class ChecklistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistItem
        fields = ['id', 'section', 'description', 'status', 'remarks']

class BatteryVoltageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BatteryVoltage
        fields = ['id', 'battery_number', 'voltage']

class ChecklistSerializer(serializers.ModelSerializer):
    items = ChecklistItemSerializer(many=True)
    batteries = BatteryVoltageSerializer(many=True)

    class Meta:
        model = Checklist
        fields = '__all__'

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        batteries_data = validated_data.pop('batteries', [])

        try:
            checklist = Checklist.objects.create(**validated_data)
        except Exception as e:
            raise ValidationError(f"Error creating Checklist: {e}")

        for item in items_data:
            try:
                ChecklistItem.objects.create(checklist=checklist, **item)
            except Exception as e:
                raise ValidationError(f"Error creating ChecklistItem: {e}")

        for battery in batteries_data:
            try:
                BatteryVoltage.objects.create(checklist=checklist, **battery)
            except Exception as e:
                raise ValidationError(f"Error creating BatteryVoltage: {e}")

        return checklist



