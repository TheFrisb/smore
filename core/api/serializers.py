from rest_framework import serializers

from core.models import Prediction


class PredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prediction
        fields = [
            "id",
            "product",
            "status",
            "league",
            "home_team",
            "away_team",
            "kickoff_date",
            "kickoff_time",
            "prediction",
            "result",
            "odds",
        ]
