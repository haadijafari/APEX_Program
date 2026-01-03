from django.contrib import admin

from apps.profiles.models import PlayerStats


class PlayerStatsInline(admin.StackedInline):
    """
    Embeds the 5 Stats directly into the Profile Page.
    Using StackedInline because it's a single 'row' of data, not a list.
    """

    model = PlayerStats
    can_delete = False
    verbose_name_plural = "Player Stats"
    fk_name = "profile"  # Explicitly link to the profile field
