from datetime import datetime, timedelta

import jdatetime
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from apps.gate.models.daily_entry import DayPage
from apps.gate.services.calendar import (
    get_current_month_info,
    get_jalali_calendar_context,
)
from apps.profiles.models import PlayerProfile
from apps.tasks.models import Habit, HabitLog


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

        # --- 2. Calendar Setup
        month_info = get_current_month_info()

        days_in_month = month_info["days_in_month"]
        month_days = month_info["month_days"]
        g_start = month_info["g_start"]
        g_end = month_info["g_end"]
        j_month_start = month_info["j_month_start"]
        j_today = month_info["j_today"]

        # --- 3. Sleep Diagram Data ---
        # Fetch DayPages for this month
        day_pages = DayPage.objects.filter(user=user, date__range=[g_start, g_end])
        sleep_map = {dp.date: dp for dp in day_pages}

        sleep_data = []
        for d in range(days_in_month):
            # Calculate date for this day index
            c_j_date = j_month_start + timedelta(days=d)
            c_g_date = c_j_date.togregorian()

            entry = sleep_map.get(c_g_date)
            duration = 0
            if entry and entry.wake_up_time and entry.sleep_time:
                # Logic: If sleep_time (last night) > wake_up_time, it crossed midnight (e.g. 23:00 -> 07:00)
                # Formula: (24 - sleep) + wake
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
        # Get active habits
        habits = Habit.objects.filter(task__profile=profile).select_related("task")

        # Fetch all logs for this month (Source of Truth)
        habit_logs = HabitLog.objects.filter(
            habit__in=habits,
            completed_at__date__range=[g_start, g_end],
        )

        # Map completions: { habit_title: { date_str: True } }
        habit_completion_map = set()
        # Map daily counts: { date_str: count }
        daily_habit_counts_map = {}
        # Map to store titles per date
        daily_habit_titles_map = {}

        for log in habit_logs:
            c_date = log.completed_at.date()
            c_date_str = c_date.strftime("%Y-%m-%d")

            # For Grid
            habit_completion_map.add((log.habit.id, c_date_str))

            # For Bar Chart
            daily_habit_counts_map[c_date_str] = (
                daily_habit_counts_map.get(c_date_str, 0) + 1
            )

            # Collect titles
            if c_date_str not in daily_habit_titles_map:
                daily_habit_titles_map[c_date_str] = []
            daily_habit_titles_map[c_date_str].append(log.habit.task.title)

        # Build Grid Structure
        habit_grid = []
        for habit in habits:
            row = []
            title = habit.task.title

            for d in range(days_in_month):
                c_j_date = j_month_start + timedelta(days=d)
                c_g_date_str = c_j_date.togregorian().strftime("%Y-%m-%d")

                is_done = (habit.id, c_g_date_str) in habit_completion_map

                # Pass object for template interactivity
                row.append({"date": c_g_date_str, "status": is_done})

            habit_grid.append({"id": habit.id, "title": title, "status": row})

        # Build Count Chart Data AND Titles Data
        habit_counts_data = []
        habit_titles_data = []

        for d in range(days_in_month):
            c_j_date = j_month_start + timedelta(days=d)
            c_g_date_str = c_j_date.togregorian().strftime("%Y-%m-%d")

            habit_counts_data.append(daily_habit_counts_map.get(c_g_date_str, 0))
            # Append list of titles (or empty list)
            habit_titles_data.append(daily_habit_titles_map.get(c_g_date_str, []))

        # --- Context Update ---
        context.update(
            {
                "today": today,
                "profile": profile,
                "has_gate_log": DayPage.objects.filter(user=user, date=today).exists(),
                # TODO: Make this 'consecutive days'
                "streak": DayPage.objects.filter(user=user).count(),
                "stat_labels": stat_labels,
                "stat_values": stat_values,
                "month_days": month_days,  # [1, 2, 3 ... 30]
                "current_month_name": j_today.strftime("%B"),
                "sleep_data": sleep_data,
                "habit_grid": habit_grid,
                "habit_counts_data": habit_counts_data,
                "habit_titles_data": habit_titles_data,
            }
        )

        # 5. Inject Calendar Data (Existing Service)
        calendar_data = get_jalali_calendar_context(user)
        context.update(calendar_data)

        return context


@login_required
@require_POST
def toggle_habit_log(request, habit_id, date_str):
    """
    AJAX Endpoint: Toggles the completion status of a habit for a specific date.
    Creates or deletes a HabitLog entry.
    """
    # Use filter().first() to avoid crash if profile doesn't exist yet (though unlikely here)
    profile = PlayerProfile.objects.filter(user=request.user).first()
    if not profile:
        return JsonResponse({"error": "Profile not found"}, status=404)

    habit = get_object_or_404(Habit, id=habit_id, task__profile=profile)

    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"error": "Invalid date format"}, status=400)

    # 1. Toggle Logic
    # Check for existing log in that day
    logs = HabitLog.objects.filter(habit=habit, completed_at__date=date_obj)

    if logs.exists():
        # Toggle OFF: Delete the log
        logs.delete()
        status = "removed"
    else:
        # If it's today, we might want to keep the exact time.
        # But for consistency with "None" request, we default to midnight for manual toggles.
        # However, to be safe, if it is today, we can use now(); otherwise midnight.
        now = timezone.now()

        if date_obj == now.date():
            log_time = now
        else:
            # Set time to 00:00:00 (Start of day)
            log_time = timezone.datetime.combine(date_obj, timezone.datetime.min.time())
            if timezone.is_aware(now):
                log_time = timezone.make_aware(log_time)

        HabitLog.objects.create(habit=habit, completed_at=log_time)
        status = "added"

    # 2. Recalculate Daily Count for Chart
    # Get all habits for this user
    all_habits = Habit.objects.filter(task__profile=profile)

    # Fetch logs to get count AND titles
    updated_logs = HabitLog.objects.filter(
        habit__in=all_habits, completed_at__date=date_obj
    ).select_related("habit__task")

    daily_count = updated_logs.count()
    daily_titles = [log.habit.task.title for log in updated_logs]

    return JsonResponse(
        {
            "status": status,
            "date": date_str,
            "habit_id": habit_id,
            "daily_count": daily_count,
            "daily_titles": daily_titles,
        }
    )
