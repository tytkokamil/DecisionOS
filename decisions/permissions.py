from __future__ import annotations

from typing import Optional

from django.contrib.auth.models import AbstractBaseUser

from .models import Team, TeamMember, Decision


def _is_authenticated(user: AbstractBaseUser) -> bool:
    try:
        return bool(user and user.is_authenticated)
    except Exception:
        return False


def _is_admin_user(user: AbstractBaseUser) -> bool:
    try:
        return bool(user.is_superuser or user.is_staff)
    except Exception:
        return False


def _get_membership(user: AbstractBaseUser, team: Team) -> Optional[TeamMember]:
    if not _is_authenticated(user):
        return None
    try:
        return TeamMember.objects.filter(team=team, user=user).first()
    except Exception:
        return None


def _role_in(member: Optional[TeamMember], roles: tuple[str, ...]) -> bool:
    if not member:
        return False
    role = getattr(member, "role", None)
    return role in roles


def can_view_team(user: AbstractBaseUser, team: Team) -> bool:
    if not _is_authenticated(user):
        return False
    if _is_admin_user(user):
        return True
    return _get_membership(user, team) is not None


def can_create_decision(user: AbstractBaseUser, team: Team) -> bool:
    if not _is_authenticated(user):
        return False
    if _is_admin_user(user):
        return True

    member = _get_membership(user, team)
    return _role_in(member, ("admin", "decision_maker", "reviewer", "member", "owner"))


def can_view_decision(user: AbstractBaseUser, decision: Decision) -> bool:
    if not _is_authenticated(user):
        return False
    if _is_admin_user(user):
        return True

    team = getattr(decision, "team", None)
    if team is None:
        return False

    return _get_membership(user, team) is not None


def can_edit_decision(user: AbstractBaseUser, decision: Decision) -> bool:
    if not can_view_decision(user, decision):
        return False
    if _is_admin_user(user):
        return True

    try:
        if decision.created_by_id == getattr(user, "id", None) and decision.status in ("draft", "review"):
            return True
    except Exception:
        pass

    member = _get_membership(user, decision.team)
    return _role_in(member, ("admin", "decision_maker", "owner"))


def can_review_decision(user: AbstractBaseUser, decision: Decision) -> bool:
    if not can_view_decision(user, decision):
        return False
    if _is_admin_user(user):
        return True

    member = _get_membership(user, decision.team)
    return _role_in(member, ("admin", "decision_maker", "reviewer", "owner"))
