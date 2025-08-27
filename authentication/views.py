import logging
from urllib.parse import urlencode, quote

import jwt
import requests as rq
from django.contrib.auth.hashers import make_password
from django.http import HttpResponse
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
APPLE_TOKEN_URL = "https://appleid.apple.com/auth/token"
APPLE_KEYS_URL = "https://appleid.apple.com/auth/keys"


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


class AppleReceiverView(APIView):
    """
    Handles Apple Sign-In for:
    - iOS native flow (id_token)
    - Android/Web flow (authorization code)
    """

    permission_classes = [AllowAny]

    def post(self, request):
        id_token_client = request.data.get("id_token")
        code = request.data.get("code")

        if not id_token_client and not code:
            return Response(
                {"error": "Missing id_token or code"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            if code:
                params = urlencode(request.data, quote_via=quote)
                deep_link = (
                    f"intent://callback?{params}#"
                    f"Intent;package=com.smore;"
                    f"scheme=signinwithapple;end"
                )
                html = f'<html><head><meta http-equiv="refresh" content="0;url={deep_link}"></head></html>'
                return HttpResponse(html, content_type="text/html")

            decoded = self._verify_token(id_token_client)

            user, created = self._get_or_create_user(decoded)

            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "username": user.username,
                    },
                }
            )

        except Exception as e:
            logger.exception("Apple Sign-In failed")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def _exchange_code_for_token(self, code: str) -> str:
        """
        Exchange authorization code for id_token via Apple API
        """
        response = rq.post(
            "https://appleid.apple.com/auth/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.APPLE_REDIRECT_URI,
                "client_id": settings.APPLE_CLIENT_ID,
                "client_secret": generate_apple_client_secret(),
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        token_data = response.json()
        id_token_client = token_data.get("id_token")
        if not id_token_client:
            raise ValueError("Apple response missing id_token")
        return id_token_client

    def _verify_token(self, id_token_client: str) -> dict:
        """
        Verify the Apple JWT using Apple's public keys
        """
        jwks_client = PyJWKClient(APPLE_KEYS_URL)
        signing_key = jwks_client.get_signing_key_from_jwt(id_token_client)
        decoded = jwt.decode(
            id_token_client,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.APPLE_CLIENT_ID,
            issuer="https://appleid.apple.com",
        )
        if "sub" not in decoded:
            raise ValueError("Apple token missing 'sub'")
        return decoded

    def _get_or_create_user(self, decoded: dict):
        """
        Get existing user by email or Apple sub, or create new one
        """
        sub = decoded.get("sub")
        email = decoded.get("email") or f"{sub}@privaterelay.appleid.com"

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email,
                "provider": User.ProviderType.APPLE,
                "apple_sub": sub,
                "is_email_verified": True,
            },
        )
        return user, created


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
