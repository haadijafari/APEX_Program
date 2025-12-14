from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PlayerProfile, UserAttribute

class PlayerProfileInline(admin.StackedInline):
    """Shows Level/Rank/Gold"""
    model = PlayerProfile
    can_delete = False
    verbose_name_plural = 'Player Status'
    fk_name = 'user'

class UserAttributeInline(admin.TabularInline):
    """Shows the dynamic list of stats (Strength, Python, etc.)"""
    model = UserAttribute
    extra = 1 # Allows adding 1 new stat easily
    verbose_name = "Attribute"
    verbose_name_plural = "Player Attributes (Stats)"

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Add both inlines
    inlines = (PlayerProfileInline, UserAttributeInline)
    
    list_display = ('username', 'get_level', 'get_rank', 'is_staff')

    def get_level(self, obj):
        return obj.profile.level
    get_level.short_description = 'Level'

    def get_rank(self, obj):
        return obj.profile.rank
    get_rank.short_description = 'Rank'
