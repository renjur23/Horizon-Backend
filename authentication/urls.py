# authentication/urls.py
from django.urls import path
from authentication.views import RegisterView, LoginView, LogoutView,GuestSummaryView,PasswordResetRequestAPIView,PasswordResetConfirmAPIView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),          
    path('register/', RegisterView.as_view(), name='register'), 
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path("guest/summary/", GuestSummaryView.as_view(), name="guest-summary"),
    path('request-reset-password/', PasswordResetRequestAPIView.as_view(), name='request-reset-password'),
    path('reset-password/<uidb64>/<token>/', PasswordResetConfirmAPIView.as_view(), name='password-reset-confirm'),
    
]
