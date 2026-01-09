from django import forms
from django.db import models
from django.urls import reverse
from django.utils.html import format_html
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

    readonly_fields = ["edit_link"]

    fields = [
        "order",
        "title",
        "primary_stat",
        "secondary_stat",
        "manual_rank",
        "edit_link",
        "is_active",
    ]
    ordering = ("order",)

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

    def edit_link(self, obj):
        if obj.pk:
            # We force the link to open the "OneTimeTask" admin view
            url = reverse("admin:tasks_onetimetask_change", args=[obj.pk])
            return format_html(
                '<a href="{}" target="_blank" class="btn btn-primary btn-sm">Edit Full Details</a>',
                url,
            )
        return "-"

    edit_link.short_description = "Actions"


class TaskLogInline(TabularInline):
    """
    Shows the history of this task (when it was completed).
    """

    model = TaskLog
    extra = 0
    can_delete = True
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
