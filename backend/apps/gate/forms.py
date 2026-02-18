from django import forms
from django.forms import HiddenInput, TextInput, inlineformset_factory
from tinymce.widgets import TinyMCE

from apps.gate.models import DailyEntry, DailyHighlight

# Create explicit choices for the Score (1-10)
RATING_CHOICES = [(i, str(i)) for i in range(1, 11)]


class DailyEntryForm(forms.ModelForm):
    class Meta:
        model = DailyEntry
        exclude = ["user", "date"]
        widgets = {
            # Use RadioSelect for the Score
            "rating": forms.RadioSelect(choices=RATING_CHOICES),
            # Switch Emoji to a Read-Only Text Input
            # And add a special ID or Class to target it with JS easily
            "emoji": forms.TextInput(
                attrs={
                    "id": "mood-picker-input",  # <--- FORCE THIS ID
                    "class": "mood-input-styled",
                    "placeholder": "😶",
                    "readonly": "readonly",
                }
            ),
            # Ensure Time inputs render as HTML5 time pickers
            "wake_up_time": forms.TimeInput(
                attrs={
                    "type": "time",
                    "class": "form-control bg-dark text-white border-secondary",
                }
            ),
            "sleep_time": forms.TimeInput(
                attrs={
                    "type": "time",
                    "class": "form-control bg-dark text-white border-secondary",
                }
            ),
            "nap_duration": forms.NumberInput(
                attrs={
                    "class": "form-control bg-dark text-white border-secondary",
                    "step": "0.1",  # Allows decimals like 0.5
                    "placeholder": "0",
                }
            ),
            # Keep the other text areas dark
            "event": forms.TextInput(
                attrs={"class": "form-control bg-dark text-white border-secondary"}
            ),
            "quote": forms.Textarea(
                attrs={
                    "class": "form-control bg-dark text-white border-secondary",
                    "rows": 2,
                }
            ),
            "lesson_of_day": forms.Textarea(
                attrs={
                    "class": "form-control bg-dark text-white border-secondary",
                    "rows": 2,
                }
            ),
            "diary": TinyMCE(
                attrs={
                    "class": "form-control bg-dark text-white border-secondary",
                    "rows": 15,
                },
                mce_attrs={
                    "height": 700,
                    "width": "100%",
                },
            ),
            "financial_notes": forms.Textarea(
                attrs={
                    "class": "form-control bg-dark text-white border-secondary",
                    "rows": 3,
                }
            ),
            "notes_tomorrow": forms.Textarea(
                attrs={
                    "class": "form-control bg-dark text-white border-secondary",
                    "rows": 3,
                }
            ),
        }


# Base widget config for the highlight rows
HighlightWidget = TextInput(
    attrs={
        "class": "form-control bg-dark text-white border-secondary",
        "placeholder": "Write here...",
        "autocomplete": "off",
    }
)

# Factory for Positives
PositiveHighlightFormSet = inlineformset_factory(
    DailyEntry,
    DailyHighlight,
    fields=["content", "category"],
    widgets={"content": HighlightWidget, "category": HiddenInput()},
    extra=0,
    can_delete=True,
)

# Factory for Negatives
NegativeHighlightFormSet = inlineformset_factory(
    DailyEntry,
    DailyHighlight,
    fields=["content", "category"],
    widgets={"content": HighlightWidget, "category": HiddenInput()},
    extra=0,
    can_delete=True,
)
