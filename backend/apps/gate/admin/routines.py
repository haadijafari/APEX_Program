from django.contrib import admin

from apps.gate.models.routines import Routine, RoutineItem


@admin.register(RoutineItem)
class RoutineItemAdmin(admin.ModelAdmin):
    """
    Admin view for RoutineItem.
    It's helpful for debugging to see all items, but they are
    best managed through the Routine admin page (using the inline).
    """

    list_display = ("title", "routine", "priority", "is_active", "created_at")
    list_filter = ("is_active", "routine")
    search_fields = ("title",)
    list_per_page = 20
    readonly_fields = ("created_at", "updated_at")


class RoutineItemInline(admin.TabularInline):
    """
    This creates an inline editor for RoutineItems
    that we can "plug in" to the Routine admin page.
    """

    model = RoutineItem

    # Fields to show for each item in the inline form
    fields = ("title", "description", "priority", "is_active")

    # How many extra blank forms to show at the bottom
    extra = 1

    # A helpful message
    verbose_name = "Routine Item"
    verbose_name_plural = "Routine Items"


@admin.register(Routine)
class RoutineAdmin(admin.ModelAdmin):
    """
    This is the main admin page for managing your routines.
    It includes the RoutineItemInline so you can edit
    a routine and all its items in one place.
    """

    # What to show in the main list of routines
    list_display = ("name", "user", "is_active", "created_at")

    # Filters for the list view
    list_filter = ("is_active", "user")

    # Search bar
    search_fields = ("name", "user__username")

    # Read-only fields in the detail view
    readonly_fields = ("created_at", "updated_at")

    # Plug in the inline editor!
    inlines = [RoutineItemInline]
