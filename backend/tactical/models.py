from django.contrib.auth.models import User
from django.db import models

class Team(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name="team")
    name = models.CharField(max_length=120)
    season = models.CharField(max_length=40, default="2025 / 26")
    style = models.CharField(max_length=120, default="Possession with patient build-up")

class Player(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="players")
    name = models.CharField(max_length=120)
    position = models.CharField(max_length=60)
    number = models.CharField(max_length=8, blank=True)
    status = models.CharField(max_length=30, default="Available")

class Opponent(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="opponents")
    name = models.CharField(max_length=120)
    formation = models.CharField(max_length=30, default="4-3-3")
    style = models.CharField(max_length=60, default="High Press")
    notes = models.TextField(blank=True)

class TacticalDecision(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="decisions")
    opponent = models.ForeignKey(Opponent, on_delete=models.PROTECT, related_name="decisions")
    opponent_formation = models.CharField(max_length=30)
    opponent_style = models.CharField(max_length=60)
    attacking_strength = models.CharField(max_length=20)
    midfield_strength = models.CharField(max_length=20)
    defensive_strength = models.CharField(max_length=20)
    team_style = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)

class Recommendation(models.Model):
    decision = models.OneToOneField(TacticalDecision, on_delete=models.CASCADE, related_name="recommendation")
    formation = models.CharField(max_length=30)
    approach = models.CharField(max_length=180)
    reason = models.TextField()
