from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Habit(models.Model):
    """
    Extends a Task to be repeating.
    """

    class Frequency(models.TextChoices):
        DAILY = "DAILY", _("Daily")
        WEEKLY = "WEEKLY", _("Weekly")
        MONTHLY = "MONTHLY", _("Monthly")

    task = models.OneToOneField(
        "tasks.Task", on_delete=models.CASCADE, related_name="habit_config"
    )

    # --- 1. Google Calendar-style Scheduling ---
    frequency = models.CharField(
        _("Frequency"),
        max_length=10,
        choices=Frequency.choices,
        default=Frequency.DAILY,
    )

    # e.g., Interval 2 + Daily = "Every 2 Days"
    interval = models.PositiveIntegerField(
        _("Repeat Every"),
        default=1,
        validators=[MinValueValidator(1)],
        help_text=_("e.g. 1 for 'Every Day', 2 for 'Every 2 Days'"),
    )

    # For Weekly: [0, 2, 4] = Mon, Wed, Fri
    # We use a JSON list of integers (0=Monday, 6=Sunday)
    weekdays = models.JSONField(
        _("On Days"),
        default=list,
        blank=True,
        help_text=_("Select specific days for Weekly frequency (0=Sat, 6=Fri)."),
    )

    time_of_day = models.TimeField(_("Time"), null=True, blank=True)

    # --- 2. Streak Tracking (Cached) ---
    # We keep these for quick UI access, but they should be updated via signals/methods
    current_streak = models.PositiveIntegerField(_("Current Streak"), default=0)
    longest_streak = models.PositiveIntegerField(_("Longest Streak"), default=0)

    # Active/Paused state
    is_active = models.BooleanField(default=True)

    # --- Timestamps ---
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    def __str__(self):
        return f"Habit: {self.task.title} ({self.get_frequency_display()})"


class HabitLog(models.Model):
    """
    Records every instance of a habit being completed.
    This solves "there is no way I can log if I have done my habit".
    """

    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name="logs")

    completed_at = models.DateTimeField(default=timezone.now)

    # Optional: Track quality/notes (e.g., "Barely did it" vs "Crushed it")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-completed_at"]
        verbose_name = "Habit Log"
        verbose_name_plural = "Habit Logs"

    def __str__(self):
        return f"{self.habit.task.title} - {self.completed_at.strftime('%Y-%m-%d')}"
