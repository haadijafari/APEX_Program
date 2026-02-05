from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.tasks.models.tasks import Task


class TaskLog(models.Model):
    """
    Unified History.
    Tracks every time a Task (or Routine Item) is completed.
    """

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="logs")
    completed_at = models.DateTimeField(
        _("Completed At"), default=timezone.now, db_index=True
    )

    # Snapshot of the reward at the moment of completion
    # (In case you change the Task rank later, history remains accurate)
    xp_earned = models.PositiveIntegerField(_("XP Earned"), default=0)

    class Meta:
        ordering = ["-completed_at"]
        verbose_name = "Task Log"
        verbose_name_plural = "Task Logs"

    def __str__(self):
        return f"{self.task.title} @ {self.completed_at.strftime('%Y-%m-%d %H:%M')}"
