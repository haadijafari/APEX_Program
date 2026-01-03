from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.models import User
from apps.profiles.admin import PlayerAttributeInline, PlayerProfileInline


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Add both inlines
    inlines = (PlayerProfileInline, PlayerAttributeInline)

    list_display = ("username", "get_level", "get_rank", "is_staff")

    def get_level(self, obj):
        return obj.profile.level

    get_level.short_description = "Level"

    def get_rank(self, obj):
        return obj.profile.rank

    get_rank.short_description = "Rank"
