from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class TemplateCategory(models.Model):
    """Categories for organizing templates"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Template Categories"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class DecisionTemplate(models.Model):
    """Reusable templates for decisions"""
    VISIBILITY_CHOICES = [
        ('public', 'Public - Available to all teams'),
        ('private', 'Private - Only visible to creator'),
        ('team', 'Team - Visible to specific teams'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(TemplateCategory, on_delete=models.SET_NULL, null=True, related_name='templates')
    
    default_title_pattern = models.CharField(max_length=200, help_text="e.g., 'Hire: {candidate_name}'")
    default_description = models.TextField(blank=True)
    
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='public')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_templates')
    is_system_template = models.BooleanField(default=False)
    
    usage_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-usage_count', '-created_at']

    def __str__(self):
        return self.name

    def increment_usage(self):
        self.usage_count += 1
        self.save(update_fields=['usage_count'])


class TemplateField(models.Model):
    """Custom fields for templates"""
    FIELD_TYPES = [
        ('text', 'Short Text'),
        ('textarea', 'Long Text'),
        ('number', 'Number'),
        ('currency', 'Currency'),
        ('date', 'Date'),
        ('select', 'Dropdown'),
        ('multiselect', 'Multiple Choice'),
        ('checkbox', 'Checkbox'),
        ('url', 'URL'),
        ('email', 'Email'),
    ]

    template = models.ForeignKey(DecisionTemplate, on_delete=models.CASCADE, related_name='fields')
    
    label = models.CharField(max_length=200)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    help_text = models.TextField(blank=True)
    placeholder = models.CharField(max_length=200, blank=True)
    
    options = models.JSONField(default=list, blank=True)
    
    is_required = models.BooleanField(default=False)
    default_value = models.TextField(blank=True)
    
    order = models.IntegerField(default=0)
    section = models.CharField(max_length=100, blank=True, help_text="Group fields into sections")

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.template.name} - {self.label}"


class TemplateFieldValue(models.Model):
    """Stores field values when a decision uses a template"""
    decision = models.ForeignKey('Decision', on_delete=models.CASCADE, related_name='template_values')
    field = models.ForeignKey(TemplateField, on_delete=models.CASCADE)
    value = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['decision', 'field']

    def __str__(self):
        return f"{self.decision.title} - {self.field.label}"
