from django.db import models
from django.utils.translation import gettext_lazy as _


class PlayerStats(models.Model):
    """
    Tracks the 5 Main Attributes and their specific XP.
    """

    class StatType(models.TextChoices):
        STR = "STR", "Physique"
        INT = "INT", "Intellect"
        CHA = "CHA", "Charisma"
        WIL = "WIL", "Discipline"
        WIS = "WIS", "Psyche"

    profile = models.OneToOneField(
        "profiles.PlayerProfile", on_delete=models.CASCADE, related_name="stats"
    )

    # --- Stats ---
    # We store Level and XP for each.
    str_level = models.PositiveIntegerField(_("Physique Level"), default=1)
    str_xp = models.PositiveIntegerField(_("Physique XP"), default=0)

    int_level = models.PositiveIntegerField(_("Intellect Level"), default=1)
    int_xp = models.PositiveIntegerField(_("Intellect XP"), default=0)

    cha_level = models.PositiveIntegerField(_("Charisma Level"), default=1)
    cha_xp = models.PositiveIntegerField(_("Charisma XP"), default=0)

    wil_level = models.PositiveIntegerField(_("Discipline Level"), default=1)
    wil_xp = models.PositiveIntegerField(_("Discipline XP"), default=0)

    wis_level = models.PositiveIntegerField(_("Psyche Level"), default=1)
    wis_xp = models.PositiveIntegerField(_("Psyche XP"), default=0)

    # --- Timestamps ---
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    def __str__(self):
        return f"Stats for {self.profile.user.username}"

    def get_xp_required(self, level):
        """
        Stat Formula: ceil( (100 * (1.06)^L * L) / 100 ) * 100
        """
        import math

        raw = 100 * (1.06**level) * level
        return math.ceil(raw / 100) * 100
