from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import CustomUser
from .serializers import (
    UserRegistrationSerializer,
    CustomTokenObtainPairSerializer
)
from .permissions import IsAdminUser, IsEmployeeUser
from .permissions import IsGuestUser
from order.models import Inverter


from rest_framework import status
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode



from django.utils.encoding import force_str

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()  # Make a mutable copy of request data
        data["user_type"] = "guest"       # Force default role to guest
        data["is_approved"] = False       # Require admin approval

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response({
            "message": "User registered successfully. Awaiting admin approval.",
            "user_id": user.id
        }, status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        user = CustomUser.objects.get(email=request.data['email'])

        response.data.update({
            'role': user.user_type,
            'name': user.email
        })
        return response


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Successfully logged out."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": "Invalid refresh token or already blacklisted."}, status=status.HTTP_400_BAD_REQUEST)







class GuestSummaryView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        try:
            hired = Inverter.objects.count()
            breakdown = Inverter.objects.filter(inverter_status__name__icontains="breakdown").count()
            operational = Inverter.objects.filter(inverter_status__name__icontains="operational").count()

            return Response({
                "hired": hired,
                "breakdown": breakdown,
                "ready to hire": operational
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        




class PasswordResetRequestAPIView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = f"https://www.horizonoffgridenergy.com/reset-password/{uid}/{token}/"



            send_mail(
                subject="Password Reset Request",
                message=f"Hi {user.email},\n\nUse the link to reset your password:\n{reset_link}\n\nIgnore if not requested.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            return Response({"message": "Password reset email sent."}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)



class PasswordResetConfirmAPIView(APIView):
     permission_classes = [AllowAny]
     
     def post(self, request, uidb64, token):
        password = request.data.get("password")
        if not password:
            return Response({"error": "Password is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)

            if not default_token_generator.check_token(user, token):
                return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(password)
            user.save()
            return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)

        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response({"error": "Invalid user or link."}, status=status.HTTP_400_BAD_REQUEST)
