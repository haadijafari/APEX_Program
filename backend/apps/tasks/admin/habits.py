from django.contrib import admin

from apps.tasks.models import Habit


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ["task", "current_streak", "frequency_summary"]

    def frequency_summary(self, obj):
        return obj.frequency_config

    frequency_summary.short_description = "Schedule"
