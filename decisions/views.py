# decisions/views.py  (GESAMTDATEI – KOMPLETT ERSETZEN)

from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views  # optional, falls du es wo brauchst
from django.db.models import Count
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import (
    Decision,
    Team,
    TeamMember,
    Notification,
    DecisionComment,
    DecisionReview,
    DecisionAudit,
)

# =========================
# Permissions (minimal, robust)
# =========================

def _is_team_member(user, team: Team) -> bool:
    return TeamMember.objects.filter(team=team, user=user).exists()

def can_view_team(user, team: Team) -> bool:
    return _is_team_member(user, team)

def can_view_decision(user, decision: Decision) -> bool:
    return _is_team_member(user, decision.team)

def can_edit_decision(user, decision: Decision) -> bool:
    # simplest rule: team member can edit (du kannst hier später Rollen prüfen)
    return _is_team_member(user, decision.team)

def can_create_decision(user, team: Team) -> bool:
    return _is_team_member(user, team)

def can_review_decision(user, decision: Decision) -> bool:
    return _is_team_member(user, decision.team)


# =========================
# Dashboard
# =========================

@login_required
def dashboard(request):
    # robust: alle Decisions in Teams, wo der user Mitglied ist
    decisions = Decision.objects.filter(team__teammember__user=request.user).distinct().order_by("-updated_at")
    return render(request, "decisions/dashboard.html", {"decisions": decisions})


# =========================
# Analytics
# =========================

@login_required
def analytics_dashboard(request):
    qs = Decision.objects.filter(team__teammember__user=request.user).distinct()

    stats = {
        "total": qs.count(),
        "draft": qs.filter(status="draft").count(),
        "review": qs.filter(status="review").count(),
        "approved": qs.filter(status="approved").count(),
        "implemented": qs.filter(status="implemented").count(),
        "rejected": qs.filter(status="rejected").count(),
        "critical": qs.filter(priority="critical").count(),
    }

    status_counts = list(qs.values("status").annotate(count=Count("id")).order_by("status"))
    priority_counts = list(qs.values("priority").annotate(count=Count("id")).order_by("priority"))

    return render(request, "decisions/analytics_dashboard.html", {
        "stats": stats,
        "status_counts": status_counts,
        "priority_counts": priority_counts,
    })


# =========================
# Teams
# =========================

@login_required
def teams_list(request):
    teams = Team.objects.filter(teammember__user=request.user).distinct().order_by("name")
    return render(request, "decisions/teams_list.html", {"teams": teams})


@login_required
def team_detail(request, pk):
    team = get_object_or_404(Team, pk=pk)
    if not can_view_team(request.user, team):
        return HttpResponseForbidden()

    members = TeamMember.objects.filter(team=team).select_related("user").order_by("role")
    decisions = Decision.objects.filter(team=team).order_by("-updated_at")

    return render(request, "decisions/team_detail.html", {
        "team": team,
        "members": members,
        "decisions": decisions,
    })


# =========================
# Decisions: list/detail/create/edit/delete/status
# =========================

@login_required
def decision_list(request):
    decisions = Decision.objects.filter(team__teammember__user=request.user).distinct().order_by("-updated_at")
    return render(request, "decisions/decision_list.html", {"decisions": decisions})


@login_required
def decision_detail(request, pk):
    decision = get_object_or_404(Decision, pk=pk)
    if not can_view_decision(request.user, decision):
        return HttpResponseForbidden()

    reviews = DecisionReview.objects.filter(decision=decision).order_by("-created_at") if "DecisionReview" in globals() else []
    comments = DecisionComment.objects.filter(decision=decision, parent__isnull=True).order_by("created_at") if "DecisionComment" in globals() else []
    audit_logs = DecisionAudit.objects.filter(decision=decision).order_by("-timestamp") if "DecisionAudit" in globals() else []

    return render(request, "decisions/decision_detail.html", {
        "decision": decision,
        "reviews": reviews,
        "comments": comments,
        "audit_logs": audit_logs,
    })


@login_required
def decision_create(request):
    if request.method == "POST":
        team = get_object_or_404(Team, pk=request.POST.get("team"))
        if not can_create_decision(request.user, team):
            return HttpResponseForbidden()

        decision = Decision.objects.create(
            title=request.POST.get("title", "").strip(),
            description=request.POST.get("description", "").strip(),
            priority=(request.POST.get("priority") or "medium"),
            status=(request.POST.get("status") or "draft"),
            team=team,
            created_by=request.user,
        )

        try:
            DecisionAudit.objects.create(
                decision=decision,
                user=request.user,
                action="created",
                changes={"title": decision.title},
                timestamp=timezone.now(),
            )
        except Exception:
            pass

        return redirect("decisions:decision_detail", pk=decision.pk)

    teams = Team.objects.filter(teammember__user=request.user).distinct().order_by("name")
    return render(request, "decisions/decision_create.html", {"teams": teams})


@login_required
def decision_edit(request, pk):
    decision = get_object_or_404(Decision, pk=pk)
    if not can_edit_decision(request.user, decision):
        return HttpResponseForbidden()

    if request.method == "POST":
        before = {"title": decision.title, "description": decision.description, "priority": decision.priority, "status": decision.status}

        decision.title = request.POST.get("title", "").strip()
        decision.description = request.POST.get("description", "").strip()
        decision.priority = request.POST.get("priority") or decision.priority
        decision.status = request.POST.get("status") or decision.status
        decision.save()

        try:
            DecisionAudit.objects.create(
                decision=decision,
                user=request.user,
                action="edited",
                changes={"before": before, "after": {"title": decision.title, "description": decision.description, "priority": decision.priority, "status": decision.status}},
                timestamp=timezone.now(),
            )
        except Exception:
            pass

        return redirect("decisions:decision_detail", pk=decision.pk)

    return render(request, "decisions/decision_edit.html", {"decision": decision})


@login_required
def decision_delete(request, pk):
    decision = get_object_or_404(Decision, pk=pk)
    if not can_edit_decision(request.user, decision):
        return HttpResponseForbidden()

    if request.method == "POST":
        try:
            DecisionAudit.objects.create(
                decision=decision,
                user=request.user,
                action="deleted",
                changes={"title": decision.title},
                timestamp=timezone.now(),
            )
        except Exception:
            pass

        decision.delete()
        return redirect("decisions:dashboard")

    return render(request, "decisions/decision_delete_confirm.html", {"decision": decision})


@login_required
def decision_change_status(request, pk):
    decision = get_object_or_404(Decision, pk=pk)
    if not can_edit_decision(request.user, decision):
        return HttpResponseForbidden()

    if request.method == "POST":
        old = decision.status
        decision.status = request.POST.get("status") or decision.status
        decision.save()

        try:
            DecisionAudit.objects.create(
                decision=decision,
                user=request.user,
                action="status_changed",
                changes={"from": old, "to": decision.status},
                timestamp=timezone.now(),
            )
        except Exception:
            pass

    return redirect("decisions:decision_detail", pk=pk)


# =========================
# Reviews
# =========================

@login_required
def decision_submit_review(request, pk):
    decision = get_object_or_404(Decision, pk=pk)
    if not can_review_decision(request.user, decision):
        return HttpResponseForbidden()

    if request.method == "POST":
        DecisionReview.objects.create(
            decision=decision,
            reviewer=request.user,
            status=request.POST.get("status") or "comment",
            comment=request.POST.get("comment") or "",
            created_at=timezone.now(),
        )
        try:
            DecisionAudit.objects.create(
                decision=decision,
                user=request.user,
                action="review_submitted",
                changes={"status": request.POST.get("status")},
                timestamp=timezone.now(),
            )
        except Exception:
            pass

    return redirect("decisions:decision_detail", pk=pk)


# =========================
# Comments
# =========================

@login_required
def decision_add_comment(request, pk):
    decision = get_object_or_404(Decision, pk=pk)
    if not can_view_decision(request.user, decision):
        return HttpResponseForbidden()

    if request.method == "POST":
        text = (request.POST.get("text") or "").strip()
        parent_id = request.POST.get("parent_id")
        parent = None
        if parent_id:
            parent = get_object_or_404(DecisionComment, pk=parent_id, decision=decision)

        DecisionComment.objects.create(
            decision=decision,
            user=request.user,
            text=text,
            parent=parent,
            created_at=timezone.now(),
            updated_at=timezone.now(),
        )

        try:
            DecisionAudit.objects.create(
                decision=decision,
                user=request.user,
                action="commented",
                changes={"text": text[:200]},
                timestamp=timezone.now(),
            )
        except Exception:
            pass

    return redirect("decisions:decision_detail", pk=pk)


# =========================
# Notifications
# =========================

@login_required
def notifications_list(request):
    notifications = Notification.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "decisions/notifications.html", {"notifications": notifications})


@login_required
def notifications_mark_read(request, pk):
    try:
        n = Notification.objects.get(pk=pk, user=request.user)
        n.is_read = True
        n.save()
    except Notification.DoesNotExist:
        pass
    return redirect("decisions:notifications_list")


@login_required
def notifications_mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect("decisions:notifications_list")


# =========================
# API – AI Quality Check (Fallback)
# =========================

@require_POST
@login_required
def api_ai_quality_check(request, pk):
    decision = get_object_or_404(Decision, pk=pk)
    if not can_view_decision(request.user, decision):
        return JsonResponse({"success": False, "message": "Forbidden"}, status=403)

    text = (decision.description or "").strip()
    score = 40
    missing = []
    suggestions = []

    if len(text) >= 200:
        score += 20
    else:
        missing.append("Mehr Kontext/Details in der Beschreibung ergänzen.")

    if "alternative" in text.lower() or "alternativen" in text.lower():
        score += 10
    else:
        missing.append("Alternativen nennen (z.B. Option A/B/C).")

    if "risik" in text.lower():
        score += 10
    else:
        missing.append("Risiken/Downsides ergänzen.")

    if "owner" in text.lower() or "verantwort" in text.lower():
        score += 10
    else:
        missing.append("Verantwortliche Person/Owner ergänzen.")

    if score > 100:
        score = 100

    if missing:
        suggestions.append("Ergänze: " + " ".join(missing))

    return JsonResponse({
        "success": True,
        "score": score,
        "missing": missing,
        "suggestions": suggestions,
        "message": "Heuristic check (AI disabled / no key required)."
    })


# =========================
# API – AI Summary (Fallback)
# =========================

@require_POST
@login_required
def api_ai_generate_summary(request, pk):
    decision = get_object_or_404(Decision, pk=pk)
    if not can_view_decision(request.user, decision):
        return JsonResponse({"success": False, "message": "Forbidden"}, status=403)

    text = (decision.description or "").strip()
    if not text:
        summary = "No description available to summarize."
    else:
        summary = text.replace("\n", " ").strip()
        if len(summary) > 400:
            summary = summary[:400].rsplit(" ", 1)[0] + "..."

    return JsonResponse({
        "success": True,
        "summary": summary,
        "message": "Heuristic summary (AI disabled / no key required)."
    })
