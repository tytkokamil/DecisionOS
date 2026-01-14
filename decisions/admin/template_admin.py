from django.contrib import admin
from decisions.models import TemplateCategory, DecisionTemplate, TemplateField, TemplateFieldValue


class TemplateFieldInline(admin.TabularInline):
    model = TemplateField
    extra = 1
    fields = ['label', 'field_type', 'is_required', 'order', 'help_text']


@admin.register(TemplateCategory)
class TemplateCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'order', 'template_count']
    list_editable = ['order']
    search_fields = ['name', 'description']
    
    def template_count(self, obj):
        return obj.templates.count()
    template_count.short_description = 'Templates'


@admin.register(DecisionTemplate)
class DecisionTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'visibility', 'usage_count', 'is_system_template', 'created_at']
    list_filter = ['category', 'visibility', 'is_system_template']
    search_fields = ['name', 'description']
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    inlines = [TemplateFieldInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category')
        }),
        ('Template Content', {
            'fields': ('default_title_pattern', 'default_description')
        }),
        ('Settings', {
            'fields': ('visibility', 'is_system_template', 'created_by')
        }),
        ('Statistics', {
            'fields': ('usage_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TemplateField)
class TemplateFieldAdmin(admin.ModelAdmin):
    list_display = ['label', 'template', 'field_type', 'is_required', 'order']
    list_filter = ['field_type', 'is_required', 'template__category']
    search_fields = ['label', 'template__name']


@admin.register(TemplateFieldValue)
class TemplateFieldValueAdmin(admin.ModelAdmin):
    list_display = ['decision', 'field', 'value_preview', 'updated_at']
    list_filter = ['field__template']
    search_fields = ['decision__title', 'field__label']
    
    def value_preview(self, obj):
        return obj.value[:50] + '...' if len(obj.value) > 50 else obj.value
    value_preview.short_description = 'Value'
