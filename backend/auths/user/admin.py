from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PlayerProfile

class PlayerProfileInline(admin.StackedInline):
    """
    Embeds the PlayerProfile form into the User form.
    """
    model = PlayerProfile
    can_delete = False
    verbose_name_plural = 'Player Status'
    fk_name = 'user'
    
    # Group stats into fieldsets for cleaner UI
    fieldsets = (
        ("Rank & Level", {
            "fields": ("level", "xp_current", "rank", "job_class", "gold")
        }),
        ("Attributes", {
            "fields": (
                ("strength", "agility", "intellect"),
                ("vitality", "perception", "luck")
            )
        }),
    )

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    The unified Admin view.
    """
    inlines = (PlayerProfileInline,)
    
    # Optional: Add Level/Rank to the list view columns
    list_display = ('username', 'email', 'get_level', 'get_rank', 'is_staff')

    def get_level(self, obj):
        return obj.profile.level
    get_level.short_description = 'Level'

    def get_rank(self, obj):
        return obj.profile.rank
    get_rank.short_description = 'Rank'
