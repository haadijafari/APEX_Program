from django import forms
from django.contrib import admin
from django.db import models
from unfold.admin import ModelAdmin, StackedInline

from apps.tasks.forms import HabitAdminForm
from apps.tasks.models import Habit, HabitLog


class HabitLogInline(StackedInline):
    model = HabitLog
    extra = 0
    # readonly_fields = ["completed_at"]  # Commented for development
    can_delete = False


@admin.register(Habit)
class HabitAdmin(ModelAdmin):
    form = HabitAdminForm

    list_display = ["get_title", "frequency", "interval", "current_streak"]
    list_filter = ["frequency", "is_active"]
    inlines = [HabitLogInline]  # Now you can see history directly in the habit page

    fieldsets = (
        ("Task Link", {"fields": ("task", "is_active")}),
        (
            "Schedule",
            {
                "fields": (
                    # Group all 4 fields in one tuple to put them on the same row.
                    # The row height will be defined by the tallest item (Weekdays).
                    ("frequency", "interval", "time_of_day", "weekdays"),
                )
            },
        ),
        ("Progress", {"fields": ("current_streak", "longest_streak")}),
    )

    # Force native time picker
    formfield_overrides = {
        models.TimeField: {
            "widget": forms.TimeInput(attrs={"type": "time", "class": "form-control"})
        },
    }

    # Inject the JavaScript file
    class Media:
        js = ("js/admin_tasks.js",)

    def get_title(self, obj):
        return obj.task.title

    get_title.short_description = "Habit"
