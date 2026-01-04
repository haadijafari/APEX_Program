from django import forms
from unfold.widgets import UnfoldAdminCheckboxSelectMultiple

from apps.tasks.models import Habit


class HabitAdminForm(forms.ModelForm):
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
        # widget=forms.CheckboxSelectMultiple,  # This renders as checkboxes
        widget=UnfoldAdminCheckboxSelectMultiple,
        required=False,
        help_text="Select the days this habit should occur.",
    )

    class Meta:
        model = Habit
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
