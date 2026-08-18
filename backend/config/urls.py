from django.urls import path
from tactical import views

urlpatterns = [
    path("", views.home_page, name="home"),
    path("login/", views.login_page, name="login"),
    path("register/", views.register_page, name="register"),
    path("logout/", views.logout_page, name="logout"),
    path("dashboard/", views.dashboard_page, name="dashboard"),
    path("team/", views.team_page, name="team"),
    path("players/", views.players_page, name="players"),
    path("opponents/", views.opponents_page, name="opponents"),
    path("analysis/", views.analysis_page, name="analysis"),
    path("recommendation/", views.recommendation_page, name="recommendation"),
    path("recommendation/<int:decision_id>/", views.recommendation_page, name="recommendation_detail"),
    path("history/", views.history_page, name="history"),
    # Existing JSON endpoints remain available for compatibility.
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
