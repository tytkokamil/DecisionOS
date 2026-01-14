# decisions/urls.py  (GESAMTDATEI – KOMPLETT ERSETZEN)

from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = "decisions"

urlpatterns = [
    # Auth
    path("login/", auth_views.LoginView.as_view(template_name="decisions/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="/decisions/login/"), name="logout"),

    # Dashboard + Analytics
    path("", views.dashboard, name="dashboard"),
    path("analytics/", views.analytics_dashboard, name="analytics_dashboard"),

    # Teams
    path("teams/", views.teams_list, name="teams_list"),
    path("teams/<int:pk>/", views.team_detail, name="team_detail"),

    # Decisions
    path("list/", views.decision_list, name="decision_list"),
    path("create/", views.decision_create, name="decision_create"),
    path("decision/<int:pk>/", views.decision_detail, name="decision_detail"),
    path("decision/<int:pk>/edit/", views.decision_edit, name="decision_edit"),
    path("decision/<int:pk>/delete/", views.decision_delete, name="decision_delete"),
    path("decision/<int:pk>/status/", views.decision_change_status, name="decision_change_status"),

    # Reviews
    path("decision/<int:pk>/review/", views.decision_submit_review, name="decision_submit_review"),

    # Comments
    path("decision/<int:pk>/comments/add/", views.decision_add_comment, name="decision_add_comment"),

    # Notifications
    path("notifications/", views.notifications, name="notifications_list"),
    path("notifications/read/<int:pk>/", views.notifications_mark_read, name="notifications_mark_read"),
    path("notifications/mark-all-read/", views.notifications_mark_all_read, name="notifications_mark_all_read"),

    # ✅ API – AI Quality Check
    path("api/ai/quality-check/<int:pk>/", views.api_ai_quality_check, name="api_ai_quality_check"),
]
