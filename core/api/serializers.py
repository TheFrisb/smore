from django.conf import settings
from rest_framework import serializers

from core.models import (
    BetLine,
    FrequentlyAskedQuestion,
    Prediction,
    SportCountry,
    SportLeague,
    SportMatch,
    SportTeam,
    Ticket,
)
from subscriptions.serializers import ProductSerializer


class PredictionSerializer2(serializers.ModelSerializer):
    class Meta:
        model = Prediction
        fields = ["id", "product", "status", "prediction", "result", "odds", "stake"]


class SportCountrySerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    class Meta:
        model = SportCountry
        fields = ("name", "logo")

    def get_logo(self, obj):
        if obj.logo and obj.logo.url:
            return f"{settings.BASE_URL}{obj.logo.url}"
        return None


class SportTeamSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    class Meta:
        model = SportTeam
        fields = ("name", "logo")

    def get_logo(self, obj):
        if obj.logo and obj.logo.url:
            return f"{settings.BASE_URL}{obj.logo.url}"
        return None


class SportLeagueSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    country = SportCountrySerializer()
    friendly_name = serializers.CharField(source="readable_name", read_only=True)

    class Meta:
        model = SportLeague
        fields = ("name", "logo", "country", "friendly_name")

    def get_logo(self, obj):
        if obj.logo and obj.logo.url:
            return f"{settings.BASE_URL}{obj.logo.url}"
        return None


class SportMatchSerializer(serializers.ModelSerializer):
    league = SportLeagueSerializer()
    home_team = SportTeamSerializer()
    away_team = SportTeamSerializer()

    class Meta:
        model = SportMatch
        fields = (
            "league",
            "home_team",
            "away_team",
            "kickoff_datetime",
            "type",
            "home_team_score",
            "away_team_score",
        )


class PredictionSerializer(serializers.ModelSerializer):
    match = SportMatchSerializer()
    product = ProductSerializer()

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
            "product",
            "stake",
        )


class FrequentlyAskedQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FrequentlyAskedQuestion
        fields = ("id", "question", "answer")


class BetLineSerializer(serializers.ModelSerializer):
    match = SportMatchSerializer()

    class Meta:
        model = BetLine
        fields = ["id", "match", "bet", "bet_type", "odds", "status"]


class TicketHistorySerializer(serializers.ModelSerializer):
    object_type = serializers.SerializerMethodField()
    product = ProductSerializer()
    bet_lines = BetLineSerializer(many=True)
    total_odds = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            "id",
            "object_type",
            "product",
            "status",
            "starts_at",
            "bet_lines",
            "total_odds",
            "visibility",
            "label",
            "stake",
        ]

    def get_object_type(self, obj):
        return "ticket"

    def get_total_odds(self, obj):
        return float(obj.total_odds)


class PredictionHistorySerializer(serializers.ModelSerializer):
    object_type = serializers.SerializerMethodField()
    match = SportMatchSerializer()
    product = ProductSerializer()
    has_analysis = serializers.SerializerMethodField()

    class Meta:
        model = Prediction
        fields = [
            "id",
            "object_type",
            "match",
            "prediction",
            "odds",
            "result",
            "status",
            "detailed_analysis",
            "product",
            "visibility",
            "stake",
        ]

    def get_object_type(self, obj):
        return "prediction"

    def has_analysis(self, obj):
        return obj.has_detailed_analysis
