from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Team, Opponent, TacticalDecision

class TemplateFlowTests(TestCase):
    def test_register_creates_user_and_team(self):
        response = self.client.post(reverse("register"), {"name":"Coach One", "email":"coach@example.com", "password":"secret123"})
        self.assertRedirects(response, reverse("dashboard"))
        self.assertTrue(User.objects.filter(username="coach@example.com").exists())
        self.assertTrue(Team.objects.filter(owner__username="coach@example.com").exists())

    def test_auth_templates_render(self):
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)
        self.assertEqual(self.client.get(reverse("register")).status_code, 200)

    def test_protected_dashboard_redirects(self):
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_dashboard_template_renders_for_authenticated_user(self):
        user = User.objects.create_user(username="render", password="secret123")
        Team.objects.create(owner=user, name="Render FC")
        self.client.login(username="render", password="secret123")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Render FC")

    def test_team_player_and_opponent_crud(self):
        user = User.objects.create_user(username="crud", password="secret123")
        Team.objects.create(owner=user, name="CRUD FC")
        self.client.login(username="crud", password="secret123")
        self.client.post(reverse("team"), {"name":"Updated FC", "season":"2026", "style":"Fast transitions"})
        self.client.post(reverse("players"), {"name":"Alex Smith", "position":"Forward", "number":"9", "status":"Available"})
        self.client.post(reverse("opponents"), {"name":"Rivals", "formation":"5-4-1", "style":"Low Block", "notes":"Compact"})
        team = Team.objects.get(owner=user)
        self.assertEqual(team.name, "Updated FC")
        self.assertEqual(team.players.count(), 1)
        self.assertEqual(team.opponents.count(), 1)
        player = team.players.first(); opponent = team.opponents.first()
        self.client.post(reverse("players"), {"player_id": player.id, "name":"Alex Updated", "position":"Forward", "number":"10", "status":"Available"})
        self.client.post(reverse("opponents"), {"opponent_id": opponent.id, "name":"Rivals Updated", "formation":"4-4-2", "style":"Possession", "notes":"Updated"})
        self.assertEqual(team.players.first().name, "Alex Updated")
        self.assertEqual(team.opponents.first().name, "Rivals Updated")
        self.client.post(reverse("players"), {"action":"delete", "player_id": player.id})
        self.client.post(reverse("opponents"), {"action":"delete", "opponent_id": opponent.id})
        self.assertEqual(team.players.count(), 0); self.assertEqual(team.opponents.count(), 0)

    def test_main_templates_render_for_authenticated_user(self):
        user = User.objects.create_user(username="pages", password="secret123")
        team = Team.objects.create(owner=user, name="Pages FC")
        Opponent.objects.create(team=team, name="Rivals")
        self.client.login(username="pages", password="secret123")
        for route in ("dashboard", "team", "players", "opponents", "analysis", "recommendation", "history"):
            response = self.client.get(reverse(route))
            self.assertEqual(response.status_code, 200, route)

    def test_analysis_saves_rule_based_recommendation(self):
        user = User.objects.create_user(username="coach", password="secret123")
        team = Team.objects.create(owner=user, name="Test FC")
        opponent = Opponent.objects.create(team=team, name="Northbridge", formation="4-3-3", style="High Press")
        self.client.login(username="coach", password="secret123")
        response = self.client.post(reverse("analysis"), {"opponent_id": opponent.id, "attacking_strength":"High", "midfield_strength":"Medium", "defensive_strength":"Medium", "team_style":team.style})
        self.assertEqual(response.status_code, 302)
        decision = TacticalDecision.objects.get(team=team)
        self.assertEqual(decision.recommendation.formation, "4-1-4-1")
