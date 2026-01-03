from django.contrib import admin

from apps.gate.models.daily_entry import DayPage


@admin.register(DayPage)
class DayPageAdmin(admin.ModelAdmin):
    list_display = ("date", "user", "rating", "emoji", "created_at")
    list_filter = ("date", "rating", "emoji")
    search_fields = ("quote", "lesson_of_day", "positives")
    date_hierarchy = "date"

    fieldsets = (
        ("Header", {"fields": ("user", "date", "event")}),
        ("Metrics", {"fields": (("wake_up_time", "sleep_time"), ("rating", "emoji"))}),
        ("Inspiration", {"fields": ("quote", "lesson_of_day")}),
        (
            "Reflections",
            {"fields": ("positives", "negatives", "financial_notes", "notes_tomorrow")},
        ),
    )
