from django import forms
from unfold.widgets import UnfoldAdminCheckboxSelectMultiple

from apps.tasks.models import Task, TaskSchedule


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = "__all__"
        widgets = {
            "effort_level": forms.NumberInput(
                attrs={
                    "type": "range",
                    "min": "1",
                    "max": "10",
                    "step": "1",
                    "class": "form-range w-full",  # Tailwind/Bootstrap utility
                    "style": "width: 100%; max-width: 300px;",
                }
            ),
            "impact_level": forms.NumberInput(
                attrs={
                    "type": "range",
                    "min": "1",
                    "max": "5",
                    "step": "1",
                    "class": "form-range w-full",
                    "style": "width: 100%; max-width: 300px;",
                }
            ),
            # Optional: Fear Factor is also great as a slider
            "fear_factor": forms.NumberInput(
                attrs={
                    "type": "range",
                    "min": "1.0",
                    "max": "2.0",
                    "step": "0.1",
                    "class": "form-range w-full",
                    "style": "width: 100%; max-width: 300px;",
                }
            ),
        }


class TaskScheduleAdminForm(forms.ModelForm):
    # Define the checkboxes with integer values
    DAYS_CHOICES = [
        (0, "Saturday"),
        (1, "Sunday"),
        (2, "Monday"),
        (3, "Tuesday"),
        (4, "Wednesday"),
        (5, "Thursday"),
        (6, "Friday"),
    ]

    # Override the model field with a MultipleChoiceField
    weekdays = forms.MultipleChoiceField(
        choices=DAYS_CHOICES,
        widget=UnfoldAdminCheckboxSelectMultiple,
        required=False,
        help_text="Select the days this habit should occur.",
    )

    class Meta:
        model = TaskSchedule
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-populate the checkboxes if editing an existing habit
        if self.instance and self.instance.pk and self.instance.weekdays:
            # The form expects a list of strings (e.g. ['0', '1']), but DB has [0, 1]
            self.initial["weekdays"] = [str(d) for d in self.instance.weekdays]

    def clean(self):
        """
        Overriding clean to enforce the rule:
        If Frequency != WEEKLY, then Weekdays MUST be empty.
        """
        cleaned_data = super().clean()
        frequency = cleaned_data.get("frequency")

        # If the user selected something other than WEEKLY, wipe the weekdays
        if frequency != "WEEKLY":
            cleaned_data["weekdays"] = []

        return cleaned_data

    def clean_weekdays(self):
        # Convert the list of strings back to a list of integers for the JSONField
        data = self.cleaned_data["weekdays"]
        return [int(d) for d in data]
