from django import forms
from django.contrib import admin
from django.db import models
from unfold.admin import ModelAdmin, TabularInline

from apps.tasks.models import Routine, RoutineItem


class RoutineItemInline(TabularInline):
    model = RoutineItem
    extra = 1
    autocomplete_fields = ["task"]
    fields = ("task", "priority", "is_active")
    ordering = ("priority",)


@admin.register(Routine)
class RoutineAdmin(ModelAdmin):
    list_display = [
        "title",
        "profile",
        "frequency",
        "time_of_day",
        "item_count",
        "is_active",
    ]
    list_filter = ["is_active", "frequency", "profile"]
    search_fields = ["title", "profile__user__username"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [RoutineItemInline]

    fieldsets = (
        (None, {"fields": ("profile", "title", "description", "is_active")}),
        (
            "Schedule",
            {
                "fields": (
                    # Grouped in one row for compactness
                    ("frequency", "interval", "time_of_day", "weekdays"),
                )
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    # Force native time picker
    formfield_overrides = {
        models.TimeField: {
            "widget": forms.TimeInput(attrs={"type": "time", "class": "form-control"})
        },
    }

    # Reuse the JS from habits to handle frequency/weekdays toggling logic
    class Media:
        js = ("js/admin_tasks.js",)

    def item_count(self, obj):
        return obj.items.count()

    item_count.short_description = "Items"


@admin.register(RoutineItem)
class RoutineItemAdmin(ModelAdmin):
    list_display = ["get_task_title", "routine", "priority", "is_active", "created_at"]
    list_filter = ["is_active", "routine"]
    search_fields = [
        "task__title",
    ]
    list_per_page = 20
    readonly_fields = ["created_at", "updated_at"]

    def get_task_title(self, obj):
        return obj.task.title

    get_task_title.short_description = "Task Title"
