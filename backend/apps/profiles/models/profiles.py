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

    # Link directly to the User in this same file
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )

    # --- Status ---
    level = models.PositiveIntegerField(default=1)
    xp_current = models.PositiveIntegerField(default=0)

    rank = models.CharField(max_length=2, choices=Rank.choices, default=Rank.E_RANK)

    job_class = models.CharField(
        max_length=50,
        default="None",
        help_text=_("e.g. Shadow Monarch, Developer, Artist"),
    )

    gold = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Level {self.level} | {self.user.username}"

    @property
    def xp_max(self):
        return self.level * 100

    @property
    def xp_percent(self):
        if self.xp_max == 0:
            return 0
        return min(100, int((self.xp_current / self.xp_max) * 100))
