from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.exceptions import PermissionDenied

class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'admin'

class IsEmployeeUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'employee'
class AdminOnlyFieldsPermission(BasePermission):
    admin_fields = {'po_number', 'contract_no', 'issued_to_id'}
    employee_fields = {
        'location_id', 'start_date', 'end_date', 'inverter_id',
        'generator_no', 'remarks', 'site_contact_id', 'fuel_price', 'co2_emission_per_litre'
    }

    def has_object_permission(self, request, view, obj):
        user = request.user
        
        if not user.is_authenticated:
            return False

        # ✅ Allow full access to admin
        if user.user_type == 'admin':
            return True

        # ✅ Employee update: must not touch admin fields, and only update allowed fields
        if user.user_type == 'employee':
            data_fields = set(request.data.keys())
            if data_fields.intersection(self.admin_fields):
                raise PermissionDenied("Employees cannot update admin-only fields.")
            if not data_fields.issubset(self.employee_fields):
                raise PermissionDenied("Some fields are not allowed to be updated by employees.")
            return True

        return False


class IsAdminOrEmployeeCanCreate(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False

        if request.method in SAFE_METHODS:
            return True  # Authenticated users can read

        if request.method == 'POST':
            return user.user_type in ['admin', 'employee']  

        if request.method in ['PUT', 'PATCH']:
            return user.user_type in ['admin', 'employee']  

        if request.method == 'DELETE':
            return user.user_type in ['admin', 'employee']

        return False
    
# permissions.py

class IsGuestUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'guest'
    

