from django.contrib import admin


class TaskTypeFilter(admin.SimpleListFilter):
    title = "Type"
    parameter_name = "type"

    def lookups(self, request, model_admin):
        return (
            ("habit", "Habits (Recurring)"),
            ("task", "One-off Tasks"),
        )

    def queryset(self, request, queryset):
        if self.value() == "habit":
            return queryset.filter(schedule__isnull=False)
        if self.value() == "task":
            return queryset.filter(schedule__isnull=True)
        return queryset
