from django import forms
from apps.daily.models.model_daypage import DayPage

class DayPageForm(forms.ModelForm):
    class Meta:
        model = DayPage
        fields = [
            'wake_up_time', 'sleep_time', 'event', 
            'quote', 'lesson_of_day', 
            'positives', 'negatives', 
            'notes_tomorrow', 'financial_notes', 
            'rating', 'emoji'
        ]
        widgets = {
            'wake_up_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'sleep_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'event': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Any special event?'}),
            'quote': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Quote of the day...'}),
            'lesson_of_day': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'positives': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'negatives': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'notes_tomorrow': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'financial_notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10}),
            'emoji': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mood emoji'}),
        }