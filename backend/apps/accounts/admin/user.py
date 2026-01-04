from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm

from apps.accounts.forms import CustomUserChangeForm, CustomUserCreationForm
from apps.accounts.models import User
from apps.profiles.admin import PlayerProfileInline

admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(ModelAdmin):
    pass


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    # Use the Unfold-compatible forms
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    change_password_form = AdminPasswordChangeForm

    # Add the Profile inline
    inlines = (PlayerProfileInline,)

    list_display = (
        "username",
        "email",
        "get_full_name",
        "get_level",
        "get_rank",
        "is_staff",
    )
    list_select_related = ("profile",)
    search_fields = ("username", "email")
    ordering = ("username",)

    # Optional Unfold Customizations
    list_filter_submit = True  # Show a submit button for filters

    def get_level(self, obj):
        # Use getattr to avoid crash if a user has no profile
        return getattr(obj.profile, "level", "-")

    get_level.short_description = "Level"

    def get_rank(self, obj):
        return getattr(obj.profile, "rank", "-")

    get_rank.short_description = "Rank"
