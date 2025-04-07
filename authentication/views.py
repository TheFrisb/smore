import logging

from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts.models import User
from accounts.serializers import UserSerializer
from accounts.services.user_service import UserService

logger = logging.getLogger(__name__)


# Create your views here.
class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]


class RefreshTokenView(TokenRefreshView):
    permission_classes = [AllowAny]


class GetMeView(APIView):
    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data, status=HTTP_200_OK)


class RegisterUserView(APIView):
    permission_classes = [AllowAny]

    class InputSerializer(serializers.Serializer):
        username = serializers.CharField()
        first_name = serializers.CharField()
        last_name = serializers.CharField()
        email = serializers.EmailField()
        password = serializers.CharField()
        confirm_password = serializers.CharField()

        def validate(self, data):
            if data["password"] != data["confirm_password"]:
                raise serializers.ValidationError("Passwords do not match.")

            if User.objects.filter(username=data["username"]).exists():
                raise serializers.ValidationError("Username already exists.")

            if User.objects.filter(email=data["email"]).exists():
                raise serializers.ValidationError("Email already exists.")

            return data

    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = User.objects.create(
            username=data["username"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            password=make_password(data["password"]),
        )

        logger.info(f"User {user.username} created.")

        return Response(status=HTTP_204_NO_CONTENT)


class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    def __init__(self):
        super().__init__()
        self.user_service = UserService()

    class InputSerializer(serializers.Serializer):
        email = serializers.EmailField()

    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = User.objects.filter(
            email=data["email"], provider=User.ProviderType.INTERNAL
        ).first()

        if user:
            logger.info(f"Password reset link sent to {user.email}")
            self.user_service.send_password_change_link(user)

        return Response(status=HTTP_204_NO_CONTENT)
