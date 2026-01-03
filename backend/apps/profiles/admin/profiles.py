from django.contrib import admin

from apps.profiles.admin.stats import PlayerStatsInline
from apps.profiles.models import PlayerProfile


class PlayerProfileInline(admin.StackedInline):
    """
    Inline to view/edit the Profile directly inside the User page.
    Note: We cannot show PlayerStats here because they are nested inside Profile.
    """

    model = PlayerProfile
    can_delete = False
    verbose_name_plural = "Player Profile"
    fk_name = "user"


@admin.register(PlayerProfile)
class PlayerProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "level", "rank", "xp_percent_display"]
    list_filter = ["rank", "level"]
    search_fields = ["user__username", "user__email"]

    # This puts the Stats form inside the Profile form
    inlines = [PlayerStatsInline]

    fieldsets = (
        ("Identity", {"fields": ("user", "avatar_img", "birth_date", "job_class")}),
        ("Progression", {"fields": ("level", "xp_current", "rank")}),
        ("Wealth", {"fields": ("net_worth",)}),
    )

    def xp_percent_display(self, obj):
        return f"{obj.xp_percent}%"

    xp_percent_display.short_description = "XP Progress"
