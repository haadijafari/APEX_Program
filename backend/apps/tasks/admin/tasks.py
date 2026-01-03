from django.contrib import admin

from apps.tasks.models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "computed_rank",
        "final_rank",
        "is_completed",
        "xp_reward_display",
    ]
    list_filter = ["is_completed", "computed_rank", "is_habit", "is_routine_item"]
    search_fields = ["title", "description"]  # Required for autocomplete_fields
    readonly_fields = ["computed_rank", "created_at", "updated_at"]

    fieldsets = (
        ("Identity", {"fields": ("profile", "title", "description")}),
        (
            "Metrics (Auto-Rank)",
            {
                "fields": (
                    "duration_minutes",
                    "effort_level",
                    "impact_level",
                    "fear_factor",
                ),
                "description": "Adjust these to change the computed rank automatically.",
            },
        ),
        ("Overrides", {"fields": ("manual_rank", "stat_rewards")}),
        ("Status", {"fields": ("is_completed", "completed_at")}),
        ("System Flags", {"fields": ("is_habit", "is_routine_item")}),
    )

    def xp_reward_display(self, obj):
        return f"{obj.xp_reward} XP"

    xp_reward_display.short_description = "XP Reward"
