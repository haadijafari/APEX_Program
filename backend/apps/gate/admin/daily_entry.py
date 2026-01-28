from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from apps.gate.models import DailyEntry, DailyHighlight


class DailyHighlightInline(TabularInline):
    model = DailyHighlight
    extra = 0
    fields = ("category", "content")
    list_display = ("category", "content")


@admin.register(DailyEntry)
class DailyEntryAdmin(ModelAdmin):
    list_display = ("date", "user", "rating", "emoji", "created_at")
    list_filter = ("date", "rating", "emoji")
    # Removed "positives" from search_fields
    search_fields = ("quote", "lesson_of_day")
    date_hierarchy = "date"

    # Add the new Inline to manage Highlights
    inlines = [DailyHighlightInline]

    fieldsets = (
        ("Header", {"fields": ("user", "date", "event")}),
        ("Metrics", {"fields": (("wake_up_time", "sleep_time"), ("rating", "emoji"))}),
        ("Inspiration", {"fields": ("quote", "lesson_of_day")}),
        (
            "Reflections",
            # Removed "positives" and "negatives" from here
            {"fields": ("financial_notes", "notes_tomorrow")},
        ),
    )
