from django.contrib import admin

from apps.tasks.models import Habit

from .base import BaseTaskAdmin
from .inlines import SubTaskInline, TaskLogInline, TaskScheduleInline


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
