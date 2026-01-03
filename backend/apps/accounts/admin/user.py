from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.models import User
from apps.profiles.admin import PlayerProfileInline


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Add the Profile inline
    inlines = (PlayerProfileInline,)

    list_display = ("username", "email", "get_level", "get_rank", "is_staff")

    # Add these to list_select_related to avoid 100+ database queries
    list_select_related = ("profile",)

    def get_level(self, obj):
        # Use getattr to avoid crash if a user has no profile
        return getattr(obj.profile, "level", "-")

    get_level.short_description = "Level"

    def get_rank(self, obj):
        return getattr(obj.profile, "rank", "-")

    get_rank.short_description = "Rank"
