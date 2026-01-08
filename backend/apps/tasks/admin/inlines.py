from django import forms
from django.db import models
from unfold.admin import StackedInline, TabularInline

from apps.tasks.forms import TaskScheduleAdminForm
from apps.tasks.models import Task, TaskLog, TaskSchedule


class SubTaskInline(TabularInline):
    """
    Allows managing subtasks (children) directly inside the parent task.
    """

    model = Task
    # Essential: tells Django this inline connects via the 'parent' field
    fk_name = "parent"
    # Clean UI: don't show empty rows by default
    extra = 0
    # Make it clickable
    show_change_link = True
    can_delete = True
    verbose_name = "Subtask"
    verbose_name_plural = "Subtasks (Checklist)"
    fields = [
        "order",
        "title",
        "primary_stat",
        "secondary_stat",
        "manual_rank",
        "is_active",
    ]
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
