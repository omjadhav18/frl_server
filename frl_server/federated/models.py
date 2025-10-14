from django.db import models
from django.conf import settings
import uuid
from accounts.models import User


class QTable(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    car = models.ForeignKey(User, on_delete=models.CASCADE, related_name="q_tables")
    track_id = models.CharField(max_length=100, null=True, blank=True)  # ✅ track/env info
    episode = models.IntegerField(default=0)  # ✅ training progress
    reward_score = models.FloatField(default=0.0)  # ✅ optional performance feedback
    q_table = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"QTable {self.id} from {self.car.email} (Track {self.track_id})"

class ClientQTable(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    run = models.ForeignKey("FederatedRun", on_delete=models.CASCADE)
    q_table = models.JSONField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"QTable from {self.client} (Run {self.run.id})"



class GlobalQTable(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    q_table = models.JSONField()
    aggregated_at = models.DateTimeField(auto_now_add=True)
    performance_score = models.FloatField(default=0.0) 


class FederatedRun(models.Model):
    """
    A training round/session initiated by the admin.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Run {self.id} - {'Active' if self.is_active else 'Completed'}"


class ClientEventLog(models.Model):
    """
    Events reported by clients (cars) during a run.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    run = models.ForeignKey(FederatedRun, on_delete=models.CASCADE, related_name="events")
    car = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=50)  # "progress", "uploaded_qtable", "test_result"
    data = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.timestamp}] Car {self.car.email} - {self.event_type}"
    

class TestResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    run = models.ForeignKey("FederatedRun", on_delete=models.CASCADE)
    episodes = models.IntegerField()
    success_rate = models.FloatField()   # e.g., percentage of successful runs
    avg_reward = models.FloatField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"TestResult {self.client} (Run {self.run.id})"
