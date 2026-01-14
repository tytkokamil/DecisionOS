from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Decision, DecisionOption
from .ai_service import ai_service

@login_required
@require_POST
def ai_analyze_decision(request, decision_id):
    """AI analysis of decision"""
    decision = Decision.objects.get(id=decision_id, team__teammember__user=request.user)
    
    analysis = ai_service.analyze_decision(decision)
    
    return JsonResponse({
        'success': True,
        'analysis': analysis
    })


@login_required
@require_POST
def ai_generate_alternatives(request, decision_id):
    """Generate alternative options with AI"""
    decision = Decision.objects.get(id=decision_id, team__teammember__user=request.user)
    
    alternatives = ai_service.generate_alternatives(decision)
    
    return JsonResponse({
        'success': True,
        'alternatives': alternatives
    })


@login_required
@require_POST
def ai_generate_summary(request, decision_id):
    """Generate executive summary"""
    decision = Decision.objects.get(id=decision_id, team__teammember__user=request.user)
    
    summary = ai_service.generate_summary(decision)
    
    return JsonResponse({
        'success': True,
        'summary': summary
    })


@login_required
@require_POST
def ai_quality_check(request, decision_id):
    """Decision Quality Check (structured + actionable)."""
    decision = Decision.objects.get(id=decision_id, team__teammember__user=request.user)
    quality = ai_service.quality_check(decision)
    return JsonResponse({
        'success': True,
        'quality': quality,
    })

@login_required
@require_POST
def ai_generate_pros_cons(request, option_id):
    """Generate pros/cons for an option"""
    option = DecisionOption.objects.get(id=option_id, decision__team__teammember__user=request.user)
    
    # Simple implementation - can be enhanced with AI later
    return JsonResponse({
        'success': True,
        'pros': ['Pro 1', 'Pro 2', 'Pro 3'],
        'cons': ['Con 1', 'Con 2', 'Con 3']
    })
