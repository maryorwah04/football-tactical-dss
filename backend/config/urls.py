from django.urls import path
from tactical import views

urlpatterns = [
    path("api/session", views.session_view),
    path("api/auth/register", views.register_view),
    path("api/auth/login", views.login_view),
    path("api/auth/logout", views.logout_view),
    path("api/workspace", views.workspace_view),
    path("api/team", views.team_view),
    path("api/players", views.players_view),
    path("api/players/<int:player_id>", views.player_detail_view),
    path("api/opponents", views.opponents_view),
    path("api/opponents/<int:opponent_id>", views.opponent_detail_view),
    path("api/analyze", views.analyze_view),
]
