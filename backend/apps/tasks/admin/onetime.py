from django.contrib import admin

from apps.tasks.models import OneTimeTask

from .base import BaseTaskAdmin
from .inlines import SubTaskInline, TaskLogInline, TaskScheduleInline


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
