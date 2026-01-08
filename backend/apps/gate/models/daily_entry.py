from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class DailyEntry(models.Model):
    """
    Represents a single day in the planner (The 'Page').
    Stores singular data points like dates, times, quotes, and reflections.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="day_pages"
    )

    # --- The Header ---
    date = models.DateField(
        default=timezone.now,
        verbose_name=_("Date"),
        help_text=_("The date this log belongs to."),
    )

    # (e.g., "Mom's Birthday", "Project Deadline")
    event = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Event / Special Occasion"),
    )

    # --- Metrics ---
    # Usually filled in the next morning or late at night
    sleep_time = models.TimeField(
        blank=True, null=True, verbose_name=_("Last Night Sleep Time")
    )

    wake_up_time = models.TimeField(
        blank=True, null=True, verbose_name=_("Wake Up Time")
    )

    nap_duration = models.FloatField(
        default=0.0, help_text="Duration in hours (e.g. 0.5 for 30 mins)"
    )

    # --- Content & Inspiration ---
    quote = models.TextField(blank=True, null=True, verbose_name=_("Quote of the Day"))

    lesson_of_day = models.TextField(
        blank=True, null=True, verbose_name=_("Lesson of the Day")
    )

    # --- Reflections ---
    # Storing these as text blocks is more flexible than 3 separate fields
    positives = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Positive Highlights"),
        help_text=_("What went well today?"),
    )

    negatives = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Negative Highlights"),
        help_text=_("What didn't go well?"),
    )

    notes_tomorrow = models.TextField(
        blank=True, null=True, verbose_name=_("Notes for Tomorrow")
    )

    financial_notes = models.TextField(
        blank=True, null=True, verbose_name=_("Financial Notes")
    )

    # --- Scoring ---
    rating = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name=_("Daily Score"),
        help_text=_("Rate your day from 1 to 10"),
    )

    emoji = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name=_("Mood Emoji"),
        help_text=_("e.g., 😎, 😴, 🚀"),
    )

    # --- Timestamps ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Day Page")
        verbose_name_plural = _("Day Pages")
        ordering = ["-date"]  # Newest days first
        # Crucial: A user creates only ONE log per specific date
        unique_together = ["user", "date"]

    def __str__(self):
        return f"{self.user.username} | {self.date}"
