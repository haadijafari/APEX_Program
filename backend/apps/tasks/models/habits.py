from django.db import models
from django.utils.translation import gettext_lazy as _


class Habit(models.Model):
    """
    Extends a Task to be repeating.
    """

    task = models.OneToOneField(
        "tasks.Task", on_delete=models.CASCADE, related_name="habit_config"
    )

    # Configuration: e.g. {'days': ['Mon', 'Wed'], 'time': '08:00'}
    frequency_config = models.JSONField(default=dict)

    current_streak = models.PositiveIntegerField(_("Current Streak"), default=0)
    longest_streak = models.PositiveIntegerField(_("Longest Streak"), default=0)

    def __str__(self):
        return f"Habit: {self.task.title}"
