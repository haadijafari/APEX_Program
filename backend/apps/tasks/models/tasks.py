from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.profiles.models import PlayerStats


class Task(models.Model):
    class Rank(models.TextChoices):
        E_RANK = "E", "E-Rank"
        D_RANK = "D", "D-Rank"
        C_RANK = "C", "C-Rank"
        B_RANK = "B", "B-Rank"
        A_RANK = "A", "A-Rank"
        S_RANK = "S", "S-Rank"
        SS_RANK = "SS", "SS-Rank"
        MONARCH = "Monarch", "Shadow Monarch"

    profile = models.ForeignKey(
        "profiles.PlayerProfile", on_delete=models.CASCADE, related_name="tasks"
    )

    title = models.CharField(_("Title"), max_length=255)
    description = models.TextField(_("Description"), blank=True)

    # --- Rewards ---
    primary_stat = models.CharField(
        _("Primary Stat"),
        max_length=3,
        choices=PlayerStats.StatType.choices,
        default=PlayerStats.StatType.STR,
        help_text=_(
            "The main stat this task develops (60% XP or 100% if no secondary)."
        ),
    )
    secondary_stat = models.CharField(
        _("Secondary Stat"),
        max_length=3,
        choices=PlayerStats.StatType.choices,
        blank=True,
        null=True,
        help_text=_("Optional. If set, it receives 40% of the XP."),
    )

    # --- Complexity Math ---
    duration_minutes = models.PositiveIntegerField(
        _("Duration Minutes"),
        default=15,
        help_text=_(
            "The duration estimated amount in minutes.\n"
            "Note: Break it into multiple tasks if it is more than 4 hours."
        ),
    )
    effort_level = models.PositiveIntegerField(
        _("Effort Level"),
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text=_("Effort level from 1 to 10."),
    )
    impact_level = models.PositiveIntegerField(
        _("Impact Level"),
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_(
            "Impact level from 1 to 5.\nNote: 5 will highly affect the calculated rank."
        ),
    )
    fear_factor = models.FloatField(
        _("Fear Factor"),
        default=1.0,
        validators=[MinValueValidator(1.0), MaxValueValidator(2.0)],
        help_text=_(
            "1.0: Routine (No Fear)\n"
            "1.5: Anxiety Inducing\n"
            "2.0: High Anxiety or Terrifying"
        ),
    )

    # --- Ranking ---
    # TODO: XP amount shown in UI for rank selection
    manual_rank = models.CharField(
        _("Manual Rank"), max_length=10, choices=Rank.choices, blank=True, null=True
    )
    computed_rank = models.CharField(
        _("Computed Rank"),
        max_length=10,
        choices=Rank.choices,
        default=Rank.E_RANK,
        editable=False,
        help_text=_("Automatically computed based on task parameters."),
    )

    # --- Status ---
    is_completed = models.BooleanField(_("Is Completed?"), default=False)
    completed_at = models.DateTimeField(_("Completed At"), null=True, blank=True)

    # --- Types ---
    is_habit = models.BooleanField(_("Is Habit?"), default=False)
    is_routine_item = models.BooleanField(_("Is Routine Item?"), default=False)

    # --- Timestamps ---
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    def __str__(self):
        return f"[{self.get_rank_display()}] {self.title}"

    @property
    def final_rank(self):
        return self.manual_rank if self.manual_rank else self.computed_rank

    @property
    def xp_reward(self):
        """
        Returns the XP value based on the Task's Rank (from Scenario).
        """
        rank_xp = {
            self.Rank.E_RANK: 15,
            self.Rank.D_RANK: 35,
            self.Rank.C_RANK: 75,
            self.Rank.B_RANK: 150,
            self.Rank.A_RANK: 350,
            self.Rank.S_RANK: 700,
            self.Rank.SS_RANK: 1200,
            self.Rank.MONARCH: 1500,
        }
        return rank_xp.get(self.final_rank, 15)

    @property
    def xp_distribution(self):
        """
        Calculates the exact XP split based on the Rank Reward and 60/40 logic.
        Returns a dict: {'STR': 45, 'INT': 30}
        """
        total_xp = self.xp_reward

        # Case 1: No Secondary Stat (or same as primary) -> 100% to Primary
        if not self.secondary_stat or self.secondary_stat == self.primary_stat:
            return {self.primary_stat: total_xp}

        # Case 2: Split 60/40
        primary_amount = int(total_xp * 0.60)
        # Give the remainder to secondary to avoid rounding loss (e.g. 75 XP -> 45 + 30)
        secondary_amount = total_xp - primary_amount

        return {
            self.primary_stat: primary_amount,
            self.secondary_stat: secondary_amount,
        }

    def calculate_score(self):
        # Score = [(Duration * 0.25) + (Effort * 1.5) + (Impact^3)] * FearFactor
        duration_score = min(
            self.duration_minutes, 240
        )  # Cap at 4 hours logic if needed, or simple scaling
        # (Simplified logic based on scenario mapping)
        base = (
            (duration_score * 0.25) + (self.effort_level * 1.5) + (self.impact_level**3)
        )
        return base * self.fear_factor

    def save(self, *args, **kwargs):
        # --- Capitalize Title ---
        if self.title:
            self.title = self.title.strip().title()

        # --- Sanity Check: Prevent redundant secondary stat ---
        # If user selects the same stat for both, treat it as Single Stat (100% Primary)
        if self.secondary_stat == self.primary_stat:
            self.secondary_stat = None

        # Calculate and set computed rank before saving
        score = self.calculate_score()
        if score <= 20:
            self.computed_rank = self.Rank.E_RANK
        elif score <= 45:
            self.computed_rank = self.Rank.D_RANK
        elif score <= 75:
            self.computed_rank = self.Rank.C_RANK
        elif score <= 120:
            self.computed_rank = self.Rank.B_RANK
        elif score <= 180:
            self.computed_rank = self.Rank.A_RANK
        elif score <= 250:
            self.computed_rank = self.Rank.S_RANK
        elif score <= 280:
            self.computed_rank = self.Rank.SS_RANK
        else:
            self.computed_rank = self.Rank.MONARCH

        super().save(*args, **kwargs)
