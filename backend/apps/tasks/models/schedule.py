from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.tasks.models.tasks import Task


def default_weekdays():
    return list(range(0, 7))


# TODO: Routines parent should not have schedule conflict with children
# TODO: Children should not have schedule at all?
class TaskSchedule(models.Model):
    """
    Defines the recurrence rules for a Task (or Routine).
    If a Task has this, it regenerates/repeats (Logic handled in Views/Services).
    """

    class Frequency(models.TextChoices):
        DAILY = "DAILY", _("Daily")
        WEEKLY = "WEEKLY", _("Weekly")
        MONTHLY = "MONTHLY", _("Monthly")
        YEARLY = "YEARLY", _("Yearly")

    task = models.OneToOneField(Task, on_delete=models.CASCADE, related_name="schedule")

    frequency = models.CharField(
        _("Frequency"),
        max_length=10,
        choices=Frequency.choices,
        default=Frequency.DAILY,
    )

    interval = models.PositiveIntegerField(
        _("Repeat Every"),
        default=1,
        help_text=_(
            "e.g.\n"
            "1 for 'Every Day/Week/Month/Year',\n"
            "2 for 'Every 2 Day/Week/Month/Year'"
        ),
    )

    # For Weekly: [0, 1] = Sat, Sun.
    weekdays = models.JSONField(
        _("On Days"),
        default=default_weekdays,
        blank=True,
        help_text=_("Select specific days for Weekly frequency."),
    )

    # Time of the Day
    start_time = models.DateTimeField(_("Start Time"), null=True, blank=True)
    end_time = models.DateTimeField(_("End Time"), null=True, blank=True)

    # --- Streaks (Unified) ---
    current_streak = models.PositiveIntegerField(_("Current Streak"), default=0)
    longest_streak = models.PositiveIntegerField(_("Longest Streak"), default=0)

    # Timestamps
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    def __str__(self):
        return f"Schedule for {self.task.title} ({self.frequency})"

    def is_due(self, date_obj=None):
        """
        Checks if the task is scheduled for the given date (default: today).
        Handles the Saturday-start mapping.
        """
        if date_obj is None:
            date_obj = timezone.localdate()

        # 1. Check Frequency
        if self.frequency == self.Frequency.DAILY:
            return True

        # 2. Check Weekly Logic
        if self.frequency == self.Frequency.WEEKLY:
            # Python: Mon=0 ... Sat=5, Sun=6
            python_day = date_obj.weekday()

            # Convert to Apex: Sat=0, Sun=1 ... Mon=2
            apex_day = (python_day + 2) % 7

            return apex_day in self.weekdays

        # TODO: Implement Monthly and Yearly

        return False
