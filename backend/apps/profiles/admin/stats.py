from unfold.admin import StackedInline

from apps.profiles.models import PlayerStats


class PlayerStatsInline(StackedInline):
    """
    Embeds the 5 Stats directly into the Profile Page.
    Using StackedInline because it's a single 'row' of data, not a list.
    """

    model = PlayerStats
    can_delete = False
    verbose_name_plural = "Player Stats"
    fk_name = "profile"  # Explicitly link to the profile field

    # Optional Unfold styling:
    tab = True  # If you want this to appear as a tab inside the profile
