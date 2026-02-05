from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.gate.models.daily_entry import DailyEntry


class DailyHighlight(models.Model):
    class Category(models.TextChoices):
        POSITIVE = "POS", _("Positive Highlight")
        NEGATIVE = "NEG", _("Negative Area to Improve")

    entry = models.ForeignKey(
        DailyEntry, on_delete=models.CASCADE, related_name="highlights"
    )
    content = models.CharField(_("Highlight"), max_length=255, blank=True)
    category = models.CharField(_("Category"), max_length=3, choices=Category.choices)
    order = models.PositiveIntegerField(_("Order"), default=0)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["entry", "category"]),
        ]
