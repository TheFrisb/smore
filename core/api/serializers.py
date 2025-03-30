from django.conf import settings
from rest_framework import serializers

from core.models import SportLeague, SportMatch, SportTeam, Prediction, SportCountry


class PredictionSerializer2(serializers.ModelSerializer):
    class Meta:
        model = Prediction
        fields = [
            "id",
            "product",
            "status",
            "prediction",
            "result",
            "odds",
        ]


class SportCountrySerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    class Meta:
        model = SportCountry
        fields = ("name", "logo")

    def get_logo(self, obj):
        return f"{settings.BASE_URL}{obj.logo.url}"


class SportTeamSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    class Meta:
        model = SportTeam
        fields = ("name", "logo")

    def get_logo(self, obj):
        return f"{settings.BASE_URL}{obj.logo.url}"


class SportLeagueSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    country = SportCountrySerializer()

    class Meta:
        model = SportLeague
        fields = ("name", "logo", "country")

    def get_logo(self, obj):
        return f"{settings.BASE_URL}{obj.logo.url}"


class SportMatchSerializer(serializers.ModelSerializer):
    league = SportLeagueSerializer()
    home_team = SportTeamSerializer()
    away_team = SportTeamSerializer()

    class Meta:
        model = SportMatch
        fields = ("league", "home_team", "away_team", "kickoff_datetime", "type")


class PredictionSerializer(serializers.ModelSerializer):
    match = SportMatchSerializer()

    class Meta:
        model = Prediction
        fields = (
            "id",
            "match",
            "prediction",
            "odds",
            "result",
            "status",
            "detailed_analysis",
        )
