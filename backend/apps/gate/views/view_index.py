from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic import TemplateView

from apps.gate.models.daily_entry import DayPage
from apps.gate.services.calendar import get_jalali_calendar_context
from apps.profiles.models import PlayerProfile


class IndexView(LoginRequiredMixin, TemplateView):
    """
    The 'Status Window' (Main Home Page).
    Aggregates Player Stats and Calendar Service data.
    """

    template_name = "gate/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # 1. Player Stats
        profile, created = PlayerProfile.objects.get_or_create(user=user)
        # Access the Stats model linked to the profile
        # We use getattr to safely handle cases where 'stats' might be missing (e.g. if signals failed)
        stats = getattr(profile, "stats", None)

        if stats:
            stat_labels = ["STR", "INT", "CHA", "WIL", "WIS"]
            stat_values = [
                stats.str_level,
                stats.int_level,
                stats.cha_level,
                stats.wil_level,
                stats.wis_level,
            ]
        else:
            # Fallback defaults if stats are missing
            stat_labels = ["STR", "INT", "CHA", "WIL", "WIS"]
            stat_values = [1, 1, 1, 1, 1]

        # 2. Simple Metrics
        today = timezone.now().date()

        context.update(
            {
                "today": today,
                "profile": profile,
                "has_gate_log": DayPage.objects.filter(user=user, date=today).exists(),
                # TODO: Make this 'consecutive days'
                "streak": DayPage.objects.filter(user=user).count(),
                # Convert attributes to lists for Chart.js
                "stat_labels": stat_labels,
                "stat_values": stat_values,
            }
        )

        # 3. Inject Calendar Data (Using our new Service)
        calendar_data = get_jalali_calendar_context(user)
        context.update(calendar_data)

        return context
