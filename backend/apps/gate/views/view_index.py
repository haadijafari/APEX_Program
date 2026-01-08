from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from apps.gate.models import DailyEntry
from apps.gate.services.calendar import (
    get_current_month_info,
    get_jalali_calendar_context,
)
from apps.profiles.models import PlayerProfile
from apps.tasks.models import Task, TaskLog


class IndexView(LoginRequiredMixin, TemplateView):
    """
    The 'Status Window' (Main Home Page).
    Aggregates Player Stats and Calendar Service data.
    """

    template_name = "gate/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.now().date()

        # --- 1. Player Stats
        profile, created = PlayerProfile.objects.get_or_create(user=user)
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
            stat_labels = ["STR", "INT", "CHA", "WIL", "WIS"]
            stat_values = [1, 1, 1, 1, 1]

        # --- 2. Calendar Setup
        month_info = get_current_month_info()
        days_in_month = month_info["days_in_month"]
        month_days = month_info["month_days"]
        g_start = month_info["g_start"]
        g_end = month_info["g_end"]
        j_month_start = month_info["j_month_start"]
        j_today = month_info["j_today"]

        # --- 3. Sleep Diagram Data ---
        daily_entries = DailyEntry.objects.filter(
            user=user, date__range=[g_start, g_end]
        )
        sleep_map = {dp.date: dp for dp in daily_entries}

        sleep_data = []
        for d in range(days_in_month):
            c_j_date = j_month_start + timedelta(days=d)
            c_g_date = c_j_date.togregorian()

            entry = sleep_map.get(c_g_date)
            duration = 0
            if entry and entry.wake_up_time and entry.sleep_time:
                wt = entry.wake_up_time
                st = entry.sleep_time
                wake_hours = wt.hour + (wt.minute / 60.0)
                sleep_hours = st.hour + (st.minute / 60.0)

                if st > wt:
                    duration = (24.0 - sleep_hours) + wake_hours
                else:
                    duration = wake_hours - sleep_hours

            sleep_data.append(round(duration, 1))

        # --- 4. Habit Grid & Habit Counts ---
        habits = Task.objects.filter(
            profile=profile,
            is_active=True,
            schedule__isnull=False,
        ).select_related("schedule")

        habit_logs = TaskLog.objects.filter(
            task__in=habits,
            completed_at__date__range=[g_start, g_end],
        ).select_related("task")

        habit_completion_map = set()
        daily_habit_counts_map = {}
        daily_habit_titles_map = {}

        for log in habit_logs:
            c_date = log.completed_at.date()
            c_date_str = c_date.strftime("%Y-%m-%d")

            # Map completions: { (task_id, date_str) }
            habit_completion_map.add((log.task.id, c_date_str))

            # Daily Counts
            daily_habit_counts_map[c_date_str] = (
                daily_habit_counts_map.get(c_date_str, 0) + 1
            )

            # Titles
            if c_date_str not in daily_habit_titles_map:
                daily_habit_titles_map[c_date_str] = []
            daily_habit_titles_map[c_date_str].append(log.task.title)

        # Build Grid
        habit_grid = []
        for habit in habits:
            row = []
            # FIX: habit is a Task object, so use habit.title directly
            title = habit.title

            for d in range(days_in_month):
                c_j_date = j_month_start + timedelta(days=d)
                c_g_date_str = c_j_date.togregorian().strftime("%Y-%m-%d")

                is_done = (habit.id, c_g_date_str) in habit_completion_map
                row.append({"date": c_g_date_str, "status": is_done})

            habit_grid.append({"id": habit.id, "title": title, "status": row})

        # Build Charts
        habit_counts_data = []
        habit_titles_data = []

        for d in range(days_in_month):
            c_j_date = j_month_start + timedelta(days=d)
            c_g_date_str = c_j_date.togregorian().strftime("%Y-%m-%d")

            habit_counts_data.append(daily_habit_counts_map.get(c_g_date_str, 0))
            habit_titles_data.append(daily_habit_titles_map.get(c_g_date_str, []))

        context.update(
            {
                "today": today,
                "profile": profile,
                "has_gate_log": DailyEntry.objects.filter(
                    user=user, date=today
                ).exists(),
                "streak": DailyEntry.objects.filter(user=user).count(),
                "stat_labels": stat_labels,
                "stat_values": stat_values,
                "month_days": month_days,
                "current_month_name": j_today.strftime("%B"),
                "sleep_data": sleep_data,
                "habit_grid": habit_grid,
                "habit_counts_data": habit_counts_data,
                "habit_titles_data": habit_titles_data,
            }
        )

        calendar_data = get_jalali_calendar_context(user)
        context.update(calendar_data)

        return context


@login_required
@require_POST
def toggle_habit_log(request, task_id, date_str):
    """
    AJAX Endpoint: Toggles the completion status of a habit.
    """
    profile = PlayerProfile.objects.filter(user=request.user).first()
    if not profile:
        return JsonResponse({"error": "Profile not found"}, status=404)

    task = get_object_or_404(Task, id=task_id, profile=profile)

    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"error": "Invalid date format"}, status=400)

    # Check for existing log
    logs = TaskLog.objects.filter(task=task, completed_at__date=date_obj)

    if logs.exists():
        # Toggle OFF
        logs.delete()
        status = "removed"
    else:
        # Toggle ON
        now = timezone.now()

        if date_obj == now.date():
            log_time = now
        else:
            # Set time to 12:00 PM to avoid timezone edge cases at midnight
            # This ensures the log stays on the correct visual "day"
            dt_naive = datetime.combine(date_obj, datetime.min.time().replace(hour=12))
            log_time = timezone.make_aware(dt_naive)

        # Create Log (Signal handles XP)
        TaskLog.objects.create(
            task=task,
            completed_at=log_time,
            # removed manual xp_earned assignment
        )
        status = "added"

    # Recalculate Daily Count
    habits = Task.objects.filter(profile=profile, schedule__isnull=False)
    updated_logs = TaskLog.objects.filter(
        task__in=habits, completed_at__date=date_obj
    ).select_related("task")

    daily_count = updated_logs.count()
    daily_titles = [log.task.title for log in updated_logs]

    return JsonResponse(
        {
            "status": status,
            "date": date_str,
            "task_id": task_id,
            "daily_count": daily_count,
            "daily_titles": daily_titles,
        }
    )
