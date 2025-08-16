from rest_framework import serializers

from .models import Log


class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Log
        fields = ["id", "user", "level", "message", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
