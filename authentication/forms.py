from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    username = forms.CharField(required=True, help_text='')  # No help text shown

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already in use. Please use a different one.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = False  # Set inactive until OTP/email verified
        if commit:
            user.save()
        return user


class EmailLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        if email and password:
            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                raise forms.ValidationError("Invalid email or password.")

            if not user.check_password(password):
                raise forms.ValidationError("Invalid email or password.")

            if not user.is_active:
                raise forms.ValidationError("Account not activated. Please verify your email.")
        return self.cleaned_data
