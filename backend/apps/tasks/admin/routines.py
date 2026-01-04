from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from apps.tasks.models import Routine, RoutineItem


class RoutineItemInline(TabularInline):
    model = RoutineItem
    extra = 1
    autocomplete_fields = ["task"]  # Uses TaskAdmin search_fields
    fields = ("task", "priority", "is_active")  # Removed 'title' and 'description'
    ordering = ("priority",)


@admin.register(Routine)
class RoutineAdmin(ModelAdmin):
    list_display = ["title", "profile", "item_count", "is_active"]
    list_filter = ["is_active", "profile"]
    search_fields = ["title", "profile__user__username"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [RoutineItemInline]

    def item_count(self, obj):
        return obj.items.count()

    item_count.short_description = "Items"


@admin.register(RoutineItem)
class RoutineItemAdmin(ModelAdmin):
    # We use 'task__title' to show the linked task's name
    list_display = ("get_task_title", "routine", "priority", "is_active", "created_at")
    list_filter = ("is_active", "routine")
    search_fields = ("task__title",)
    list_per_page = 20
    readonly_fields = ("created_at", "updated_at")

    def get_task_title(self, obj):
        return obj.task.title

    get_task_title.short_description = "Task Title"
