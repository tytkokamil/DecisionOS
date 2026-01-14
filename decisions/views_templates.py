from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from .models import DecisionTemplate, TemplateCategory, Decision, Team, TemplateFieldValue

@login_required
def template_library(request):
    """Browse available templates"""
    templates = DecisionTemplate.objects.filter(
        models.Q(visibility='public') | 
        models.Q(created_by=request.user)
    ).select_related('category')
    
    category_id = request.GET.get('category')
    if category_id:
        templates = templates.filter(category_id=category_id)
    
    search = request.GET.get('search')
    if search:
        templates = templates.filter(
            models.Q(name__icontains=search) |
            models.Q(description__icontains=search)
        )
    
    categories = TemplateCategory.objects.all()
    
    context = {
        'templates': templates,
        'categories': categories,
        'selected_category': category_id,
    }
    return render(request, 'decisions/template_library.html', context)


@login_required
def template_detail(request, template_id):
    """View template details"""
    template = get_object_or_404(DecisionTemplate, id=template_id)
    fields = template.fields.all()
    
    context = {
        'template': template,
        'fields': fields,
    }
    return render(request, 'decisions/template_detail.html', context)


@login_required
def create_from_template(request, template_id):
    """Create a decision from template"""
    template = get_object_or_404(DecisionTemplate, id=template_id)
    
    if request.method == 'POST':
        team_id = request.POST.get('team')
        team = get_object_or_404(Team, id=team_id)
        
        decision = Decision.objects.create(
            title=request.POST.get('title', template.default_title_pattern),
            description=request.POST.get('description', template.default_description),
            team=team,
            template=template,
            created_by=request.user,
            status='draft'
        )
        
        for field in template.fields.all():
            field_value = request.POST.get(f'field_{field.id}')
            if field_value:
                TemplateFieldValue.objects.create(
                    decision=decision,
                    field=field,
                    value=field_value
                )
        
        template.increment_usage()
        
        messages.success(request, f'Decision created from template: {template.name}')
        return redirect('decisions:decision_detail', pk=decision.id)
    
    user_teams = Team.objects.filter(teammember__user=request.user)
    
    context = {
        'template': template,
        'fields': template.fields.all(),
        'teams': user_teams,
    }
    return render(request, 'decisions/create_from_template.html', context)