from django.db import models
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import timedelta
from .models import Decision, DecisionAudit, Team, DecisionReview

class AnalyticsService:
    
    def get_dashboard_metrics(self, teams):
        """Aggregate metrics for a set of teams."""
        decisions = Decision.objects.filter(team__in=teams)
        total = decisions.count()
        by_status = dict(decisions.values('status').annotate(c=Count('id')).values_list('status','c'))
        by_priority = dict(decisions.values('priority').annotate(c=Count('id')).values_list('priority','c'))
        # Average cycle time (created -> decided) in days for decided decisions
        decided = decisions.filter(decided_at__isnull=False)
        avg_days = None
        if decided.exists():
            avg = decided.annotate(days=models.ExpressionWrapper((models.F('decided_at') - models.F('created_at')), output_field=models.DurationField())).aggregate(avg=Avg('days'))['avg']
            if avg is not None:
                avg_days = avg.total_seconds() / 86400.0
        return {
            'total': total,
            'by_status': by_status,
            'by_priority': by_priority,
            'avg_cycle_days': avg_days,
        }


    
    def get_team_kpis(self, team):
        """Get team KPIs"""
        decisions = Decision.objects.filter(team=team)
        
        total = decisions.count()
        completed = decisions.filter(decided_at__isnull=False).count()
        pending = decisions.filter(status='draft').count()
        
        return {
            'total_decisions': total,
            'completed': completed,
            'pending': pending,
        }
    
    def get_user_stats(self, user):
        """Get user statistics"""
        decisions_created = Decision.objects.filter(created_by=user).count()
        
        reviews_done = DecisionReview.objects.filter(
            reviewer=user, 
            status__in=['approved', 'rejected']
        ).count()
        
        reviews_pending = DecisionReview.objects.filter(
            reviewer=user,
            status='pending'
        ).count()
        
        return {
            'decisions_created': decisions_created,
            'reviews_done': reviews_done,
            'reviews_pending': reviews_pending,
        }

analytics_service = AnalyticsService()