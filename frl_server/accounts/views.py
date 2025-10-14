from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework import status
from .models import User
from .serializers import * 

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        refresh = RefreshToken.for_user(user)

        return Response({
            "user": UserSerializer(user).data,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        })

class AdminRegisterView(generics.CreateAPIView):
    """
    Handles admin registration.
    POST /api/v1/accounts/admin/register/
    """
    def post(self, request):
        data = request.data
        required_fields = ["email", "full_name", "password"]
        for field in required_fields:
            if field not in data or not data[field]:
                return Response(
                    {"error": f"'{field}' is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        email = data["email"]
        full_name = data["full_name"]
        password = data["password"]

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "A user with this email already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create user (admin)
        user = User.objects.create_user(
            email=email,
            full_name=full_name,
            password=password,
            role='ADMIN',   
        )

        return Response(
            {
                "message": "Admin registered successfully.",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_superuser": user.is_superuser
                }
            },
            status=status.HTTP_201_CREATED
        )


class AdminLoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        user = authenticate(request, email=email, password=password)

        if not user or user.role != "ADMIN":
            return Response({"error": "Invalid credentials or not an Admin"}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(user).data,
        }
        return Response(data, status=status.HTTP_200_OK)