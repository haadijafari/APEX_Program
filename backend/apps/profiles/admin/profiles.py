from django.contrib import admin

from apps.profiles.models import PlayerProfile


class PlayerProfileInline(admin.StackedInline):
    """Shows Level/Rank/Gold"""

    model = PlayerProfile
    can_delete = False
    verbose_name_plural = "Player Status"
    fk_name = "user"
