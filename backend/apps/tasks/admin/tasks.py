from django import forms
from django.contrib import admin
from django.db import models
from django.db.models import Count
from django.utils.html import format_html
from unfold.admin import ModelAdmin, StackedInline, TabularInline

from apps.tasks.forms import TaskForm, TaskScheduleAdminForm
from apps.tasks.models import Habit, OneTimeTask, Task, TaskLog, TaskSchedule


class SubTaskInline(TabularInline):
    """
    Allows managing subtasks (children) directly inside the parent task.
    """

    model = Task
    fk_name = (
        # Essential: tells Django this inline connects via the 'parent' field
        "parent"
    )
    extra = 0  # Clean UI: don't show empty rows by default
    verbose_name = "Subtask"
    verbose_name_plural = "Subtasks (Checklist)"
    fields = ["order", "title", "effort_level", "is_active"]
    ordering = ("order",)

    classes = ["collapse"]

    # Optional: Unfold styling improvements for compact inputs
    formfield_overrides = {
        models.CharField: {
            "widget": forms.TextInput(
                attrs={"class": "form-control", "style": "min-width: 300px;"}
            )
        },
        models.IntegerField: {
            "widget": forms.NumberInput(
                attrs={"class": "form-control", "style": "width: 80px;"}
            )
        },
    }


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

    classes = ["collapse"]


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

    classes = ["collapse"]

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


class TaskTypeFilter(admin.SimpleListFilter):
    title = "Type"
    parameter_name = "type"

    def lookups(self, request, model_admin):
        return (
            ("habit", "Habits (Recurring)"),
            ("task", "One-off Tasks"),
        )

    def queryset(self, request, queryset):
        if self.value() == "habit":
            return queryset.filter(schedule__isnull=False)
        if self.value() == "task":
            return queryset.filter(schedule__isnull=True)
        return queryset


class BaseTaskAdmin(ModelAdmin):
    """
    Base configuration shared between Habits and One-Time Tasks.
    """

    form = TaskForm
    search_fields = ["title", "description"]
    readonly_fields = [
        "computed_rank_display",
        "created_at",
        "updated_at",
        "xp_distribution_display",
    ]

    # Common Fieldsets
    fieldsets = (
        (
            "Main Task Info",
            {
                "fields": (
                    ("title", "is_active"),  # Row 1: Title | Status
                    "description",  # Row 2: Description (Full Width)
                    ("manual_rank", "primary_stat"),  # Row 3: Rank | Primary
                    (
                        "xp_distribution_display",
                        "secondary_stat",
                    ),  # Row 4: XP | Secondary
                )
            },
        ),
        (
            "Metrics (Auto-Rank)",
            {
                "fields": (
                    ("duration_minutes", "effort_level"),
                    ("fear_factor", "impact_level"),
                    "computed_rank_display",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    class Media:
        js = ("js/admin_tasks.js",)

    def save_model(self, request, obj, form, change):
        """
        Automatically assign the Profile of the logged-in User.
        """
        # TODO: Apply only for normal users, not superusers/admins
        if not obj.pk:  # If creating a new object
            # Assumes the logged-in user has a PlayerProfile created
            # If not, this will raise an error (which is good, admins need profiles)
            obj.profile = request.user.profile
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        """Optimize queries for all children"""
        qs = super().get_queryset(request)
        return qs.select_related("schedule").annotate(subtask_count=Count("subtasks"))

    # --- Shared Display Methods ---
    def xp_reward_display(self, obj):
        return f"{obj.xp_reward} XP"

    xp_reward_display.short_description = "Total XP"

    def computed_rank_display(self, obj):
        # We wrap the value in a span with a specific class/ID so JS can find it
        return format_html(
            '<span class="readonly" id="computed-rank-preview">{}</span>',
            obj.get_computed_rank_display(),
        )

    computed_rank_display.short_description = "Computed Rank"

    def stats_display(self, obj):
        if obj.secondary_stat:
            return f"{obj.primary_stat} / {obj.secondary_stat}"
        return obj.primary_stat

    stats_display.short_description = "Stats"

    def xp_distribution_display(self, obj):
        """
        Renders a span with a specific ID so JS can update it live.
        """
        dist = obj.xp_distribution
        text = ", ".join([f"{k}: {v} XP" for k, v in dist.items()])

        # We wrap it in a span with a unique ID
        return format_html(
            '<span id="xp-distribution-preview" style="font-weight:bold; color:#2c3e50;">{}</span>',
            text,
        )

    xp_distribution_display.short_description = "XP Split (Preview)"
    xp_distribution_display.allow_tags = True

    def subtask_count_display(self, obj):
        return obj.subtask_count

    subtask_count_display.short_description = "Subtasks"
    subtask_count_display.admin_order_field = "subtask_count"


# --- Specific Admin Implementations ---


@admin.register(Habit)
class HabitAdmin(BaseTaskAdmin):
    """
    Admin View specifically for Habits (Recurring Tasks).
    """

    list_display = [
        "title",
        "frequency_display",  # Custom for Habits
        "final_rank",
        "xp_reward_display",
        "is_active",
    ]
    list_filter = ["schedule__frequency", "is_active", "primary_stat"]

    # Habits MUST have a schedule editor
    inlines = [TaskScheduleInline, SubTaskInline, TaskLogInline]

    def get_queryset(self, request):
        # SHOW ONLY: Items that HAVE a schedule
        return super().get_queryset(request).filter(schedule__isnull=False)

    def frequency_display(self, obj):
        return (
            f"{obj.schedule.get_frequency_display()}"
            if hasattr(obj, "schedule")
            else "-"
        )

    frequency_display.short_description = "Frequency"


@admin.register(OneTimeTask)
class OneTimeTaskAdmin(BaseTaskAdmin):
    """
    Admin View specifically for Single Tasks.
    """

    list_display = [
        "title",
        "final_rank",
        "stats_display",
        "xp_reward_display",
        "subtask_count_display",
        "is_active",
    ]
    list_filter = ["is_active", "primary_stat", "computed_rank"]

    # We still allow TaskScheduleInline.
    # If user fills it, the task will technically 'move' to the Habit view after save.
    inlines = [TaskScheduleInline, SubTaskInline, TaskLogInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # 1. SHOW ONLY: Items that do NOT have a schedule
        qs = qs.filter(schedule__isnull=True)

        # 2. HIDE: Subtasks (keep main list clean)
        if request.resolver_match and request.resolver_match.url_name.endswith(
            "changelist"
        ):
            return qs.filter(parent__isnull=True)

        return qs
