from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from accounts.models import User


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = User.USERNAME_FIELD

    def validate(self, attrs):
        login = attrs.get("username")
        password = attrs.get("password")

        user = User.objects.filter(username=login).first() \
               or User.objects.filter(email=login).first()

        if not user:
            raise serializers.ValidationError(_("No active account found with the given credentials"))

        credentials = {
            User.USERNAME_FIELD: user.username,
            "password": password
        }
        user = authenticate(**credentials)

        if not user:
            raise serializers.ValidationError(_("Invalid credentials"))

        data = super().validate({
            "username": user.username,
            "password": password
        })
        return data
