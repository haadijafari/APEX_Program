from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class PlayerProfile(models.Model):
    """
    Holds the 'Meta' stats: Level, Rank, Gold, Job.
    Attributes are now in a separate model.
    """

    class Rank(models.TextChoices):
        E_RANK = "E", "E-Rank"
        D_RANK = "D", "D-Rank"
        C_RANK = "C", "C-Rank"
        B_RANK = "B", "B-Rank"
        A_RANK = "A", "A-Rank"
        S_RANK = "S", "S-Rank"
        NATIONAL = "SS", "National Level"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )

    # --- Identity ---
    avatar_img = models.ImageField(
        _("Avatar Image"), upload_to="avatars/", blank=True, null=True
    )
    birth_date = models.DateField(_("Birth Date"), blank=True, null=True)

    # --- Progression ---
    level = models.PositiveIntegerField(_("Level"), default=1)
    xp_current = models.PositiveIntegerField(_("Current XP"), default=0)
    rank = models.CharField(
        _("Rank"), max_length=10, choices=Rank.choices, default=Rank.E_RANK
    )

    job_class = models.CharField(
        _("Job/Class"),
        max_length=50,
        default="None",
        help_text=_("e.g. Shadow Monarch, Developer, Artist"),
    )

    # --- Wealth (Linked to Inventory) ---
    net_worth = models.DecimalField(
        _("Net Worth"), max_digits=12, decimal_places=2, default=0
    )

    # --- Timestamps ---
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    def __str__(self):
        return f"Level {self.level} | {self.user.username}"

    @property
    def xp_required(self):
        """
        Scenario Formula: min( ceil(100 * (1.06)^Level / 100) * 100, 30000 )
        """
        import math

        raw_xp = 100 * (1.06**self.level)
        # Round up to nearest 100
        rounded = math.ceil(raw_xp / 100) * 100
        # Clamp to 30,000 max (Novice protection is handled by math naturally > 100)
        return min(rounded, 30000)

    @property
    def xp_percent(self):
        if self.xp_required == 0:
            return 0
        return min(100, int((self.xp_current / self.xp_required) * 100))
