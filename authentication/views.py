import logging

import jwt
from django.contrib.auth.hashers import make_password
from google.auth.transport import requests
from google.oauth2 import id_token
from jwt import PyJWKClient
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts.models import User
from accounts.serializers import UserSerializer
from accounts.services.user_service import UserService
from authentication.serializers import CustomTokenObtainPairSerializer
from authentication.utils import generate_apple_client_secret
from backend import settings

logger = logging.getLogger(__name__)


# Create your views here.
class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer


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


APPLE_TOKEN_URL = "https://appleid.apple.com/auth/token"
APPLE_KEYS_URL = "https://appleid.apple.com/auth/keys"


class AppleReceiverView(APIView):
    """
    Handles Apple Sign-In for both iOS (direct id_token) and Android/web (authorization code).
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Expects either:
        - `id_token` (iOS)
        - `code` (Android / web)
        """
        id_token_internal = request.data.get("id_token")
        code = request.data.get("code")

        if not id_token_internal and not code:
            return Response(
                {"error": "Missing id_token or code"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if code and not id_token_internal:
            try:
                response = requests.post(
                    APPLE_TOKEN_URL,
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": settings.APPLE_REDIRECT_URI,
                        "client_id": settings.APPLE_CLIENT_ID,
                        "client_secret": generate_apple_client_secret(),
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

                if response.status_code != 200:
                    logger.error(f"Apple token exchange failed: {response.text}")
                    return Response(
                        {"error": "Failed to exchange code for id_token"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                token_data = response.json()
                id_token_internal = token_data.get("id_token")

                if not id_token_internal:
                    return Response(
                        {"error": "Apple response missing id_token"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            except Exception as e:
                logger.exception("Error exchanging Apple code for id_token")
                return Response({"error": "Failed to verify Apple code"}, status=400)

        # Validate the id_token
        try:
            jwks_client = PyJWKClient(APPLE_KEYS_URL)
            signing_key = jwks_client.get_signing_key_from_jwt(id_token_internal)
            decoded = jwt.decode(
                id_token_internal,
                signing_key.key,
                algorithms=["RS256"],
                audience=settings.APPLE_CLIENT_ID,
                issuer="https://appleid.apple.com",
            )
        except Exception as e:
            logger.exception("Invalid Apple ID token")
            return Response(
                {"error": "Invalid Apple token"}, status=status.HTTP_400_BAD_REQUEST
            )

        sub = decoded.get("sub")
        email = decoded.get("email") or f"{sub}@privaterelay.appleid.com"

        if not sub:
            return Response(
                {"error": "Apple token missing sub"}, status=status.HTTP_400_BAD_REQUEST
            )

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email,
                "provider": User.ProviderType.APPLE,
                "apple_sub": sub,
                "is_email_verified": True,
            },
        )

        if created:
            logger.info(f"User {user.username} created via Apple OAuth")
        else:
            logger.info(f"User {user.username} logged in via Apple OAuth")

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                },
            }
        )


class GoogleReceiverView(APIView):
    """
    Receives a Google ID token from client, verifies it,
    creates/logs in the user, and returns JWT tokens.
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        credential = request.data.get("credentials")  # Flutter sends this

        if not credential:
            logger.error("Google Login called without idToken.")
            return Response(
                {"error": "Missing idToken"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user_data = id_token.verify_oauth2_token(
                credential, requests.Request(), settings.GOOGLE_MOBILE_CLIENT_ID
            )
        except ValueError as e:
            logger.error(f"Invalid Google credential: {e}")
            return Response(
                {"error": "Invalid credential"}, status=status.HTTP_400_BAD_REQUEST
            )

        logger.info(f"Google token verified: {user_data}")

        email = user_data.get("email")
        sub = user_data.get("sub")

        if not email:
            return Response(
                {"error": "Google token has no email"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email,
                "provider": (
                    getattr(User, "ProviderType", {}).GOOGLE
                    if hasattr(User, "ProviderType")
                    else "google"
                ),
                "google_sub": sub,
                "is_email_verified": True,
            },
        )

        if created:
            logger.info(f"User {user.username} created via Google OAuth")
        else:
            logger.info(f"User {user.username} logged in via Google OAuth")

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                },
            }
        )
