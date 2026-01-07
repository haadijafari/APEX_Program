from django import forms
from django.contrib import admin
from django.db import models
from django.db.models import Count
from unfold.admin import ModelAdmin, StackedInline, TabularInline

from apps.tasks.forms import TaskScheduleAdminForm
from apps.tasks.models import Task, TaskLog, TaskSchedule


class TaskLogInline(TabularInline):
    """
    Shows the history of this task (when it was completed).
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
    Presence of this inline turns a Task into a "Habit" (or Routine).
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
                    ("frequency", "interval", "weekdays"),
                    ("start_time", "end_time"),
                    ("current_streak", "longest_streak"),
                )
            },
        ),
    )

    # Force native time picker for better UX
    formfield_overrides = {
        models.TimeField: {
            "widget": forms.TimeInput(attrs={"type": "time", "class": "form-control"})
        },
    }


@admin.register(Task)
class TaskAdmin(ModelAdmin):
    list_display = [
        "title",
        "final_rank",
        "stats_display",
        "xp_reward_display",
        "get_type_display",  # Visual indicator (Routine/Habit/Task)
        "is_active",
    ]

    list_filter = [
        "is_active",
        "primary_stat",
        "computed_rank",
        # Helper filter to see only Habits (Tasks with schedules)
        ("schedule", admin.EmptyFieldListFilter),
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
                    ("parent", "order"),
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
                "classes": ("collapse",),
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

    # --- Performance Optimization ---
    def get_queryset(self, request):
        """
        Fixes N+1 Query problem.
        1. Selects related 'schedule' so hasattr(self, 'schedule') is instant.
        2. Annotates 'subtask_count' so self.subtasks.exists() logic is instant.
        """
        qs = super().get_queryset(request)
        return qs.select_related("schedule").annotate(subtask_count=Count("subtasks"))

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
        dist = obj.xp_distribution
        return ", ".join([f"{k}: {v}" for k, v in dist.items()])

    xp_distribution_display.short_description = "XP Split (Preview)"

    def get_type_display(self, obj):
        """
        Visual indicator of what this Task 'is'.
        Uses the optimized properties from the Model.
        """
        labels = []
        if obj.is_routine:
            labels.append("📂 Routine")
        elif obj.is_habit:  # 'elif' because routines are also habits, but we prioritize the routine label or show both
            labels.append("🔄 Habit")

        # If it's a subtask (has a parent), add a small marker
        if obj.parent:
            labels.append("↳ Subtask")

        if not labels:
            return "Task"

        return " ".join(labels)

    get_type_display.short_description = "Type"
