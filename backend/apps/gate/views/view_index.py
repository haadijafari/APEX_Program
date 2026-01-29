from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from apps.gate.models import DailyEntry
from apps.gate.services import calendar as calendar_service
from apps.gate.services import index as index_service


class IndexView(LoginRequiredMixin, TemplateView):
    """
    The 'Status Window' (Main Home Page).
    Aggregates Player Stats and Calendar Service data.
    """

    template_name = "index/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.now().date()

        # 1. Calendar Setup
        month_info = calendar_service.get_current_month_info()

        # 2. Service Calls
        player_context = index_service.get_player_stats(user)
        sleep_data = index_service.get_sleep_data(user, month_info)
        habit_context = index_service.get_habit_grid_context(
            user, player_context["profile"], month_info
        )
        calendar_data = calendar_service.get_jalali_calendar_context(user)

        # 3. Simple Streak Data
        has_gate_log = DailyEntry.objects.filter(user=user, date=today).exists()
        streak_count = DailyEntry.objects.filter(user=user).count()

        # 4. Merge Everything
        context.update(
            {
                "today": today,
                "has_gate_log": has_gate_log,
                "streak": streak_count,
                "month_days": month_info["month_days"],
                "current_month_name": month_info["j_today"].strftime("%B"),
                "current_day_number": month_info["j_today"].day,
                "sleep_data": sleep_data,
                **player_context,
                **habit_context,
                **calendar_data,
            }
        )

        return context


@login_required
@require_POST
def toggle_habit_log(request, task_id, date_str):
    """
    AJAX Endpoint: Toggles the completion status of a habit.
    """
    try:
        data = index_service.perform_habit_toggle(request.user, task_id, date_str)
        return JsonResponse(data)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        # Generic catch for unexpected errors
        return JsonResponse(
            {"error": "An unexpected error occurred.", "details": str(e)}, status=500
        )
