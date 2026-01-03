from django.conf import settings
from django.db import models


class PlayerStats(models.Model):
    """
    Dynamic stats. The user can have 'Strength', 'Python', 'Charisma', etc.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attributes"
    )

    name = models.CharField(max_length=50)  # e.g. "Intellect"
    value = models.PositiveIntegerField(default=10)
    description = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ["user", "name"]  # Can't have two "Strength" stats
        ordering = ["name"]

    def __str__(self):
        return f"{self.name}: {self.value}"
