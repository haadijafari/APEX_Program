from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic import TemplateView

from apps.accounts.models import PlayerProfile
from apps.gate.models.daily_entry import DayPage
from apps.gate.services.calendar import get_jalali_calendar_context


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
        attributes = user.attributes.all()

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
                "stat_labels": [attr.name for attr in attributes],
                "stat_values": [attr.value for attr in attributes],
            }
        )

        # 3. Inject Calendar Data (Using our new Service)
        calendar_data = get_jalali_calendar_context(user)
        context.update(calendar_data)

        return context
