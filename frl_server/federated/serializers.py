from rest_framework import serializers
from .models import *


class QTableSerializer(serializers.ModelSerializer):
    car_email = serializers.EmailField(source="car.email", read_only=True)

    class Meta:
        model = QTable
        fields = [
            "id", "car", "car_email", "track_id", "episode",
            "reward_score", "q_table", "created_at"
        ]
        read_only_fields = ["id", "car", "car_email", "created_at"]

class ClientEventLogSerializer(serializers.ModelSerializer):
    car_email = serializers.CharField(source="car.email", read_only=True)

    class Meta:
        model = ClientEventLog
        fields = ["id", "car_email", "event_type", "data", "timestamp"]


class ClientQTableSerializer(serializers.ModelSerializer):
    client_email = serializers.EmailField(source="client.email", read_only=True)
    run_id = serializers.UUIDField(source="run.id", read_only=True)

    class Meta:
        model = ClientQTable
        fields = ["id", "client_email", "run_id", "q_table", "uploaded_at"]


class GlobalQTableSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalQTable
        fields = ["id", "q_table", "aggregated_at", "performance_score"]


class TestResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestResult
        fields = [
            "id",
            "client",
            "run",
            "episodes",
            "success_rate",
            "avg_reward",
            "uploaded_at",
        ]

class FederatedRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = FederatedRun
        fields = ["id", "started_at", "ended_at", "is_active"]


class ClientEventLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientEventLog
        fields = ["id", "run", "car", "event_type", "data", "timestamp"]