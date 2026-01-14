from django import forms

from .models import Decision, DecisionOption


class DecisionForm(forms.ModelForm):
    class Meta:
        model = Decision
        fields = ['title', 'description', 'status', 'priority', 'due_date', 'assigned_to', 'tags', 'impact_score']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
            'tags': forms.TextInput(attrs={'class': 'form-control'}),
            'impact_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
        }


class DecisionOptionForm(forms.ModelForm):
    class Meta:
        model = DecisionOption
        fields = ['title', 'description', 'pros', 'cons', 'estimated_cost', 'estimated_time', 'is_selected']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'pros': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'cons': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'estimated_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'estimated_time': forms.TextInput(attrs={'class': 'form-control'}),
            'is_selected': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
