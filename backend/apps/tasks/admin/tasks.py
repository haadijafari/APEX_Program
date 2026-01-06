from django import forms
from django.contrib import admin
from django.db import models
from unfold.admin import ModelAdmin, StackedInline, TabularInline

from apps.tasks.forms import TaskScheduleAdminForm
from apps.tasks.models import Task, TaskLog, TaskSchedule


class TaskLogInline(TabularInline):
    """
    Shows the history of this task (when it was completed).
    Replaces the old 'RoutineLog' and 'HabitLog'.
    """

    model = TaskLog
    extra = 0
    can_delete = False
    readonly_fields = ["completed_at", "xp_earned"]
    ordering = ("-completed_at",)

    verbose_name = "Completion History"
    verbose_name_plural = "Completion History"


class TaskScheduleInline(StackedInline):
    """
    Embeds the schedule settings directly into the Task page.
    Presence of this inline turns a Task into a "Habit".
    """

    model = TaskSchedule
    form = TaskScheduleAdminForm
    extra = 0
    can_delete = True
    verbose_name = "Schedule (Habit Config)"
    verbose_name_plural = "Schedule (Habit Config)"

    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("frequency", "interval", "start_time", "weekdays"),
                    ("current_streak", "longest_streak"),
                )
            },
        ),
    )

    # Force native time picker
    formfield_overrides = {
        models.TimeField: {
            "widget": forms.TimeInput(attrs={"type": "time", "class": "form-control"})
        },
    }

    class Media:
        js = ("js/admin_tasks.js",)


@admin.register(Task)
class TaskAdmin(ModelAdmin):
    list_display = [
        "title",
        "final_rank",
        "stats_display",
        "xp_reward_display",
        "get_type_display",  # Helper to show if it's a Routine/Habit/Task
        "is_active",
    ]

    list_filter = [
        "is_active",
        "primary_stat",
        "computed_rank",
        # Custom filters could be added here for "Is Habit" or "Is Routine"
    ]

    search_fields = ["title", "description"]

    readonly_fields = [
        "computed_rank",
        "created_at",
        "updated_at",
        "xp_distribution_display",
    ]

    inlines = [TaskScheduleInline, TaskLogInline]

    fieldsets = (
        (
            "Identity",
            {
                "fields": (
                    "profile",
                    "title",
                    "description",
                    ("parent", "order"),  # Hierarchy fields
                )
            },
        ),
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
                "classes": ("collapse",),  # Optional: collapsible
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
        ("Status", {"fields": ("is_active",)}),
    )

    # --- Custom Display Methods ---

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
        return ", ".join([f"{k}: {v}" for k, v in dist.items()])

    xp_distribution_display.short_description = "XP Split (Preview)"

    def get_type_display(self, obj):
        """
        Visual indicator of what this Task 'is'.
        """
        labels = []
        if obj.is_routine:
            labels.append("📂 Routine")
        if obj.is_habit:
            labels.append("🔄 Habit")
        if not labels:
            labels.append("task")

        return " & ".join(labels)

    get_type_display.short_description = "Type"
