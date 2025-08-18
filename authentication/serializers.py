from rest_framework import serializers
from .models import CustomUser
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'user_type', 'name']
        extra_kwargs = {
            'user_type': {'default': 'guest'},
            'name': {'required': True}
        }

    def create(self, validated_data):
        user_type = validated_data.get('user_type','guest')  
        name = validated_data.get('name', '')
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            user_type=user_type,
            name=name,
        )
        user.is_active = False 
        user.is_approved = False
        user.save()

        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
     def validate(self, attrs):
        data = super().validate(attrs)

        if not self.user.is_approved:
            raise AuthenticationFailed('Your account is pending approval.', code='authorization')

        data['role'] = self.user.user_type
        data['name'] = self.user.email
        return data
