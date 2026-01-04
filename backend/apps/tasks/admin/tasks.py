from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.tasks.models import Task


@admin.register(Task)
class TaskAdmin(ModelAdmin):
    list_display = [
        "title",
        "computed_rank",
        "final_rank",
        "stats_display",  # Show stats in list
        "is_completed",
        "xp_reward_display",
    ]
    list_filter = ["is_completed", "computed_rank", "primary_stat", "is_habit"]
    search_fields = ["title", "description"]
    readonly_fields = [
        "computed_rank",
        "created_at",
        "updated_at",
        "xp_distribution_display",  # Show the calculated split
    ]

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
        (
            "Rewards",
            {
                "fields": (
                    "manual_rank",
                    "primary_stat",
                    "secondary_stat",
                    "xp_distribution_display",
                )
            },
        ),
        ("Status", {"fields": ("is_completed", "completed_at")}),
        ("System Flags", {"fields": ("is_habit", "is_routine_item")}),
    )

    def xp_reward_display(self, obj):
        return f"{obj.xp_reward} XP"

    xp_reward_display.short_description = "Total XP"

    def stats_display(self, obj):
        if obj.secondary_stat:
            return f"{obj.primary_stat} / {obj.secondary_stat}"
        return obj.primary_stat

    stats_display.short_description = "Stats"

    def xp_distribution_display(self, obj):
        """Shows the calculated split in the admin form"""
        dist = obj.xp_distribution
        # Formats as: "STR: 45, INT: 30"
        return ", ".join([f"{k}: {v}" for k, v in dist.items()])

    xp_distribution_display.short_description = "XP Split (Preview)"
