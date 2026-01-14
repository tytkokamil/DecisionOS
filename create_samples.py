from decisions.models import TemplateCategory, DecisionTemplate, TemplateField
from django.contrib.auth import get_user_model

User = get_user_model()
admin = User.objects.filter(is_superuser=True).first()

# Create categories
hiring = TemplateCategory.objects.get_or_create(
    name='Hiring',
    defaults={'icon': '👥', 'description': 'Candidate evaluation templates', 'order': 1}
)[0]

investment = TemplateCategory.objects.get_or_create(
    name='Investment',
    defaults={'icon': '💰', 'description': 'Investment decision templates', 'order': 2}
)[0]

product = TemplateCategory.objects.get_or_create(
    name='Product',
    defaults={'icon': '🚀', 'description': 'Product development templates', 'order': 3}
)[0]

# Create Hiring Template
hiring_template = DecisionTemplate.objects.get_or_create(
    name='Candidate Evaluation',
    defaults={
        'description': 'Structured template for evaluating job candidates with consistent criteria.',
        'category': hiring,
        'default_title_pattern': 'Hire: {candidate_name} - {position}',
        'default_description': 'Evaluate candidate qualifications and cultural fit.',
        'visibility': 'public',
        'created_by': admin,
        'is_system_template': True
    }
)[0]

# Add fields to hiring template
TemplateField.objects.get_or_create(
    template=hiring_template,
    label='Candidate Name',
    defaults={'field_type': 'text', 'is_required': True, 'order': 1}
)
TemplateField.objects.get_or_create(
    template=hiring_template,
    label='Position',
    defaults={'field_type': 'text', 'is_required': True, 'order': 2}
)
TemplateField.objects.get_or_create(
    template=hiring_template,
    label='Years of Experience',
    defaults={'field_type': 'number', 'is_required': True, 'order': 3}
)
TemplateField.objects.get_or_create(
    template=hiring_template,
    label='Expected Salary',
    defaults={'field_type': 'currency', 'order': 4}
)

print('✅ Sample templates created!')
