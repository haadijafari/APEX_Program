from django.db.models import Count
from django.utils.html import format_html
from unfold.admin import ModelAdmin

from apps.tasks.forms import TaskForm


class BaseTaskAdmin(ModelAdmin):
    """
    Base configuration shared between Habits and One-Time Tasks.
    """

    form = TaskForm
    search_fields = ["title", "description"]
    readonly_fields = [
        "computed_rank_display",
        "created_at",
        "updated_at",
        "xp_distribution_display",
    ]

    fieldsets = (
        (
            "Main Task Info",
            {
                "fields": (
                    ("title", "is_active"),
                    "description",
                    ("manual_rank", "primary_stat"),
                    (
                        "xp_distribution_display",
                        "secondary_stat",
                    ),
                )
            },
        ),
        (
            "Metrics (Auto-Rank)",
            {
                "fields": (
                    ("duration_minutes", "effort_level"),
                    ("fear_factor", "impact_level"),
                    "computed_rank_display",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    class Media:
        js = ("js/admin_tasks.js",)

    def save_model(self, request, obj, form, change):
        """
        Automatically assign the Profile of the logged-in User.
        """
        # TODO: Apply only for normal users, not superusers/admins
        if not obj.pk:  # If creating a new object
            # Assumes the logged-in user has a PlayerProfile created
            # If not, this will raise an error (which is good, admins need profiles)
            obj.profile = request.user.profile
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        """Optimize queries for all children"""
        qs = super().get_queryset(request)
        return qs.select_related("schedule").annotate(subtask_count=Count("subtasks"))

    # --- Shared Display Methods ---
    def xp_reward_display(self, obj):
        return f"{obj.xp_reward} XP"

    xp_reward_display.short_description = "Total XP"

    def computed_rank_display(self, obj):
        # We wrap the value in a span with a specific class/ID so JS can find it
        return format_html(
            '<span class="readonly" id="computed-rank-preview">{}</span>',
            obj.get_computed_rank_display(),
        )

    computed_rank_display.short_description = "Computed Rank"

    def stats_display(self, obj):
        if obj.secondary_stat:
            return f"{obj.primary_stat} / {obj.secondary_stat}"
        return obj.primary_stat

    stats_display.short_description = "Stats"

    def xp_distribution_display(self, obj):
        """
        Renders a span with a specific ID so JS can update it live.
        """
        dist = obj.xp_distribution
        text = ", ".join([f"{k}: {v} XP" for k, v in dist.items()])

        # Wrap it in a span with a unique ID
        return format_html(
            '<span id="xp-distribution-preview" style="font-weight:bold; color:#2c3e50;">{}</span>',
            text,
        )

    xp_distribution_display.short_description = "XP Split (Preview)"
    xp_distribution_display.allow_tags = True

    def subtask_count_display(self, obj):
        return obj.subtask_count

    subtask_count_display.short_description = "Subtasks"
    subtask_count_display.admin_order_field = "subtask_count"
