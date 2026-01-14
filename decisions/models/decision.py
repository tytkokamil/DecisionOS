from django.db import models
from django.contrib.auth import get_user_model

import re

User = get_user_model()


class Team(models.Model):
    """Organization Teams/Departments"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.name


class TeamMember(models.Model):
    """Team membership with roles"""
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('decision_maker', 'Entscheider'),
        ('reviewer', 'Reviewer'),
        ('observer', 'Beobachter'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'team']

    def __str__(self):
        return f"{self.user.username} - {self.team.name} ({self.role})"


class Decision(models.Model):
    """Core Decision Object"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('review', 'In Review'),
        ('approved', 'Approved'),
        ('implemented', 'Implemented'),
        ('rejected', 'Rejected'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='decisions')
    template = models.ForeignKey('DecisionTemplate', on_delete=models.SET_NULL, null=True, blank=True, related_name='decisions')

    # Status & Priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')

    # People
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_decisions')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_decisions')

    # Dates
    due_date = models.DateTimeField(null=True, blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Additional
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    impact_score = models.IntegerField(default=0, help_text="Expected impact (0-100)")

    class Meta:
        ordering = ['-created_at']

    @property
    def duration_days(self):
        """Days from created_at until decided_at (or today if not decided)."""
        from datetime import date
        start = self.created_at.date() if self.created_at else date.today()
        end = self.decided_at.date() if self.decided_at else date.today()
        return max((end - start).days, 0)

    def __str__(self):
        return self.title


class DecisionOption(models.Model):
    """Options/Alternatives for a decision"""
    decision = models.ForeignKey(Decision, on_delete=models.CASCADE, related_name='options')
    title = models.CharField(max_length=200)
    description = models.TextField()
    pros = models.TextField(blank=True)
    cons = models.TextField(blank=True)
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    estimated_time = models.CharField(max_length=100, blank=True)
    votes = models.IntegerField(default=0)
    is_selected = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.decision.title} - {self.title}"


class DecisionReview(models.Model):
    """Review/Approval workflow"""
    REVIEW_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('changes_requested', 'Changes Requested'),
    ]

    decision = models.ForeignKey(Decision, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=REVIEW_STATUS, default='pending')
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.decision.title} - {self.reviewer.username} ({self.status})"


class DecisionAudit(models.Model):
    """Audit trail for all decision changes"""
    decision = models.ForeignKey(Decision, on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100)
    changes = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    @property
    def details(self):
        """Backwards-compatible human-readable summary derived from changes."""
        if not self.changes:
            return ''
        # common patterns: {'field': {'from': x, 'to': y}}
        parts = []
        for key, val in self.changes.items():
            if isinstance(val, dict) and 'from' in val and 'to' in val:
                parts.append(f"{key}: {val.get('from')} → {val.get('to')}")
            else:
                parts.append(f"{key}: {val}")
        return '; '.join(parts)

    def __str__(self):
        return f"{self.decision.title} - {self.action} by {self.user}"


class DecisionAttachment(models.Model):
    """File attachments for decisions"""
    decision = models.ForeignKey(Decision, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='decisions/attachments/')
    filename = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.decision.title} - {self.filename}"


class DecisionComment(models.Model):
    """Comments (with optional threading) for a decision."""
    decision = models.ForeignKey(Decision, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='decision_comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        prefix = f"Reply to #{self.parent_id}" if self.parent_id else "Comment"
        return f"{prefix} by {self.user.username} on {self.decision.title}"

    @staticmethod
    def extract_mentions(text: str):
        """Return a set of usernames mentioned as @username in the given text."""
        if not text:
            return set()
        # Django usernames commonly allow letters, digits and @/./+/-/_ depending on auth backend.
        # We'll keep it permissive and let DB filtering validate existence.
        return set(re.findall(r'@([\w.@+-]+)', text))

class Notification(models.Model):
    """In-app notifications for users."""
    TYPE_CHOICES = [
        ('status_change', 'Status Change'),
        ('review_assigned', 'Review Assigned'),
        ('mention', 'Mention'),
        ('deadline', 'Deadline'),
        ('system', 'System'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    decision = models.ForeignKey(Decision, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    notif_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='system')
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.title}"
