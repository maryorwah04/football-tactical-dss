import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import Team, Player, Opponent, TacticalDecision, Recommendation


def body(request):
    try: return json.loads(request.body or "{}")
    except json.JSONDecodeError: return {}

def require_team(request):
    if not request.user.is_authenticated: return None
    team, _ = Team.objects.get_or_create(owner=request.user, defaults={"name": "Riverside Athletic"})
    return team

def session_view(request):
    return JsonResponse({"authenticated": request.user.is_authenticated, "user": {"name": request.user.get_full_name() or request.user.username, "email": request.user.email} if request.user.is_authenticated else None})

@csrf_exempt
def register_view(request):
    data = body(request); email = data.get("email", "").strip().lower(); name = data.get("name", "Coach").strip(); password = data.get("password", "password")
    if not email or User.objects.filter(username=email).exists(): return JsonResponse({"error": "An account with this email already exists."}, status=400)
    user = User.objects.create_user(username=email, email=email, password=password, first_name=name)
    Team.objects.create(owner=user, name="Riverside Athletic")
    login(request, user); return JsonResponse({"ok": True})

@csrf_exempt
def login_view(request):
    data = body(request); user = authenticate(username=data.get("email", "").strip().lower(), password=data.get("password", ""))
    if not user:
        email = data.get("email", "").strip().lower(); password = data.get("password", "")
        if email and password and not User.objects.filter(username=email).exists():
            user = User.objects.create_user(username=email, email=email, password=password, first_name="Coach")
            Team.objects.create(owner=user, name="Riverside Athletic")
        else:
            return JsonResponse({"error": "Invalid email or password."}, status=400)
    login(request, user); return JsonResponse({"ok": True})

def logout_view(request): logout(request); return JsonResponse({"ok": True})

def serialize(team):
    return {"team": {"id": team.id, "name": team.name, "season": team.season, "style": team.style}, "players": list(team.players.values("id", "name", "position", "number", "status")), "opponents": list(team.opponents.values("id", "name", "formation", "style", "notes")), "decisions": [{"id": d.id, "opponent": d.opponent.name, "date": d.created_at.strftime("%d %b %Y"), "formation": d.recommendation.formation, "approach": d.recommendation.approach, "reason": d.recommendation.reason, "inputs": f"{d.opponent_formation} · {d.opponent_style} · {d.attacking_strength} attack"} for d in team.decisions.select_related("opponent", "recommendation").order_by("-created_at")]}

@csrf_exempt
def workspace_view(request):
    team = require_team(request)
    if not team: return JsonResponse({"error": "Authentication required"}, status=401)
    if request.method == "POST":
        data = body(request); incoming = data.get("team", {})
        team.name = incoming.get("name", team.name); team.season = incoming.get("season", team.season); team.style = incoming.get("style", team.style); team.save()
        incoming_player_ids = {item.get("id") for item in data.get("players", []) if item.get("id")}
        Player.objects.filter(team=team).exclude(id__in=incoming_player_ids).delete()
        for item in data.get("players", []):
            if item.get("id") and Player.objects.filter(id=item["id"], team=team).exists():
                Player.objects.filter(id=item["id"], team=team).update(name=item.get("name", ""), position=item.get("position", "Midfielder"), number=item.get("number", ""), status=item.get("status", "Available"))
            elif item.get("name"):
                Player.objects.create(team=team, name=item.get("name", ""), position=item.get("position", "Midfielder"), number=item.get("number", ""), status=item.get("status", "Available"))
        incoming_opponent_ids = {item.get("id") for item in data.get("opponents", []) if item.get("id")}
        Opponent.objects.filter(team=team).exclude(id__in=incoming_opponent_ids).delete()
        for item in data.get("opponents", []):
            if item.get("id") and Opponent.objects.filter(id=item["id"], team=team).exists():
                Opponent.objects.filter(id=item["id"], team=team).update(name=item.get("name", ""), formation=item.get("formation", "4-3-3"), style=item.get("style", "High Press"), notes=item.get("notes", ""))
            elif item.get("name"):
                Opponent.objects.create(team=team, name=item.get("name", ""), formation=item.get("formation", "4-3-3"), style=item.get("style", "High Press"), notes=item.get("notes", ""))
    return JsonResponse(serialize(team))

@csrf_exempt
def team_view(request):
    team = require_team(request)
    if not team: return JsonResponse({"error": "Authentication required"}, status=401)
    if request.method == "POST":
        data = body(request); team.name = data.get("name", team.name); team.season = data.get("season", team.season); team.style = data.get("style", team.style); team.save()
    return JsonResponse({"team": {"id": team.id, "name": team.name, "season": team.season, "style": team.style}})

@csrf_exempt
def players_view(request):
    team = require_team(request)
    if not team: return JsonResponse({"error": "Authentication required"}, status=401)
    if request.method == "POST":
        data = body(request); player = Player.objects.create(team=team, name=data.get("name", ""), position=data.get("position", "Midfielder"), number=data.get("number", ""), status=data.get("status", "Available")); return JsonResponse({"id": player.id})
    return JsonResponse({"players": list(team.players.values("id", "name", "position", "number", "status"))})

@csrf_exempt
def player_detail_view(request, player_id):
    team = require_team(request); player = Player.objects.filter(id=player_id, team=team).first()
    if not player: return JsonResponse({"error": "Player not found"}, status=404)
    if request.method == "DELETE": player.delete(); return JsonResponse({"ok": True})
    data = body(request); [setattr(player, key, data[key]) for key in ("name", "position", "number", "status") if key in data]; player.save(); return JsonResponse({"ok": True})

@csrf_exempt
def opponents_view(request):
    team = require_team(request)
    if not team: return JsonResponse({"error": "Authentication required"}, status=401)
    if request.method == "POST":
        data = body(request); opponent = Opponent.objects.create(team=team, name=data.get("name", ""), formation=data.get("formation", "4-3-3"), style=data.get("style", "High Press"), notes=data.get("notes", "")); return JsonResponse({"id": opponent.id})
    return JsonResponse({"opponents": list(team.opponents.values("id", "name", "formation", "style", "notes"))})

@csrf_exempt
def opponent_detail_view(request, opponent_id):
    team = require_team(request); opponent = Opponent.objects.filter(id=opponent_id, team=team).first()
    if not opponent: return JsonResponse({"error": "Opponent not found"}, status=404)
    if request.method == "DELETE": opponent.delete(); return JsonResponse({"ok": True})
    data = body(request); [setattr(opponent, key, data[key]) for key in ("name", "formation", "style", "notes") if key in data]; opponent.save(); return JsonResponse({"ok": True})

@csrf_exempt
def analyze_view(request):
    team = require_team(request)
    if not team: return JsonResponse({"error": "Authentication required"}, status=401)
    data = body(request); opponent = Opponent.objects.filter(id=data.get("opponent_id"), team=team).first()
    if not opponent: return JsonResponse({"error": "Opponent not found"}, status=400)
    attack, midfield, defence = data.get("attacking_strength", "Medium"), data.get("midfield_strength", "Medium"), data.get("defensive_strength", "Medium")
    formation, approach, reason = "4-2-3-1", "Controlled build-up and midfield support", "The recommendation provides additional midfield stability against a strong pressing opponent."
    if opponent.style == "Low Block" or opponent.formation == "5-4-1": formation, approach, reason = "4-3-3", "Width, patient circulation, and late runs", "The recommendation creates width and extra movement to stretch a compact defensive block."
    elif opponent.style == "Counter Attack" or attack == "High": formation, approach, reason = "4-1-4-1", "Rest defence with measured progression", "The recommendation keeps protection behind the ball while allowing controlled progression into midfield."
    elif opponent.style == "Possession": formation, approach, reason = "4-4-2", "Compact pressing and quick transitions", "The recommendation gives the team a compact reference shape and clear transition outlets."
    decision = TacticalDecision.objects.create(team=team, opponent=opponent, opponent_formation=opponent.formation, opponent_style=opponent.style, attacking_strength=attack, midfield_strength=midfield, defensive_strength=defence, team_style=data.get("team_style", team.style))
    rec = Recommendation.objects.create(decision=decision, formation=formation, approach=approach, reason=reason)
    return JsonResponse({"id": decision.id, "formation": rec.formation, "approach": rec.approach, "reason": rec.reason})


def rule_recommendation(opponent, attack, midfield, defence):
    formation = "4-2-3-1"
    approach = "Controlled build-up and midfield support"
    reason = "The recommendation provides additional midfield stability against a strong pressing opponent."
    if opponent.style == "Low Block" or opponent.formation == "5-4-1":
        formation, approach, reason = "4-3-3", "Width, patient circulation, and late runs", "The recommendation creates width and extra movement to stretch a compact defensive block."
    elif opponent.style == "Counter Attack" or attack == "High":
        formation, approach, reason = "4-1-4-1", "Rest defence with measured progression", "The recommendation keeps protection behind the ball while allowing controlled progression into midfield."
    elif opponent.style == "Possession":
        formation, approach, reason = "4-4-2", "Compact pressing and quick transitions", "The recommendation gives the team a compact reference shape and clear transition outlets."
    return formation, approach, reason


def page_context(request, **extra):
    team = require_team(request)
    context = serialize(team) if team else {"team": None, "players": [], "opponents": [], "decisions": []}
    context.update(extra)
    return context

def home_page(request):
    return redirect("dashboard" if request.user.is_authenticated else "login")

def login_page(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower(); password = request.POST.get("password", "")
        user = authenticate(username=email, password=password)
        if user:
            login(request, user); return redirect("dashboard")
        messages.error(request, "Invalid email or password.")
    return render(request, "auth/login.html")

def register_page(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        name = request.POST.get("name", "").strip(); email = request.POST.get("email", "").strip().lower(); password = request.POST.get("password", "")
        if not name or not email or not password:
            messages.error(request, "Name, email, and password are required.")
        elif User.objects.filter(username=email).exists():
            messages.error(request, "An account with this email already exists.")
        else:
            user = User.objects.create_user(username=email, email=email, password=password, first_name=name)
            Team.objects.create(owner=user, name="Riverside Athletic")
            login(request, user); return redirect("dashboard")
    return render(request, "auth/register.html")

@login_required
def logout_page(request):
    logout(request); return redirect("login")

@login_required
def dashboard_page(request):
    return render(request, "dashboard.html", page_context(request, active="dashboard"))

@login_required
def team_page(request):
    team = require_team(request)
    if request.method == "POST":
        team.name = request.POST.get("name", team.name).strip() or team.name
        team.season = request.POST.get("season", team.season).strip() or team.season
        team.style = request.POST.get("style", team.style)
        team.save(); messages.success(request, "Team details saved.")
    return render(request, "team.html", page_context(request, active="teams"))

@login_required
def players_page(request):
    team = require_team(request)
    if request.method == "POST":
        action = request.POST.get("action", "save"); player_id = request.POST.get("player_id")
        if action == "delete" and player_id:
            Player.objects.filter(id=player_id, team=team).delete(); messages.success(request, "Player removed.")
        elif request.POST.get("name", "").strip():
            player = Player.objects.filter(id=player_id, team=team).first() if player_id else Player(team=team)
            player.name = request.POST.get("name", "").strip(); player.position = request.POST.get("position", "Midfielder"); player.number = request.POST.get("number", ""); player.status = request.POST.get("status", "Available"); player.save(); messages.success(request, "Player saved.")
        return redirect("players")
    return render(request, "players.html", page_context(request, active="players"))

@login_required
def opponents_page(request):
    team = require_team(request)
    if request.method == "POST":
        action = request.POST.get("action", "save"); opponent_id = request.POST.get("opponent_id")
        if action == "delete" and opponent_id:
            Opponent.objects.filter(id=opponent_id, team=team).delete(); messages.success(request, "Opponent removed.")
        elif request.POST.get("name", "").strip():
            opponent = Opponent.objects.filter(id=opponent_id, team=team).first() if opponent_id else Opponent(team=team)
            opponent.name = request.POST.get("name", "").strip(); opponent.formation = request.POST.get("formation", "4-3-3"); opponent.style = request.POST.get("style", "High Press"); opponent.notes = request.POST.get("notes", ""); opponent.save(); messages.success(request, "Opponent profile saved.")
        return redirect("opponents")
    return render(request, "opponents.html", page_context(request, active="opponents"))

@login_required
def analysis_page(request):
    context = page_context(request, active="analysis")
    if request.method == "POST":
        opponent = get_object_or_404(Opponent, id=request.POST.get("opponent_id"), team=require_team(request))
        attack = request.POST.get("attacking_strength", "Medium"); midfield = request.POST.get("midfield_strength", "Medium"); defence = request.POST.get("defensive_strength", "Medium")
        formation, approach, reason = rule_recommendation(opponent, attack, midfield, defence)
        decision = TacticalDecision.objects.create(team=require_team(request), opponent=opponent, opponent_formation=opponent.formation, opponent_style=opponent.style, attacking_strength=attack, midfield_strength=midfield, defensive_strength=defence, team_style=request.POST.get("team_style", require_team(request).style))
        Recommendation.objects.create(decision=decision, formation=formation, approach=approach, reason=reason)
        return redirect("recommendation_detail", decision_id=decision.id)
    return render(request, "analysis.html", context)

@login_required
def recommendation_page(request, decision_id=None):
    team = require_team(request)
    decision = team.decisions.select_related("opponent", "recommendation").filter(id=decision_id).first() if decision_id else team.decisions.select_related("opponent", "recommendation").first()
    return render(request, "recommendation.html", page_context(request, active="history", decision=decision))

@login_required
def history_page(request):
    return render(request, "history.html", page_context(request, active="history"))
