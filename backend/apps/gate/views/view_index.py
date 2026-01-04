from datetime import timedelta

import jdatetime
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic import TemplateView

from apps.gate.models.daily_entry import DayPage
from apps.gate.services.calendar import get_jalali_calendar_context
from apps.profiles.models import PlayerProfile
from apps.tasks.models import Habit, Task


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
        # We need the start and end of the current Jalali month for querying
        j_today = jdatetime.date.fromgregorian(date=today)
        j_month_start = j_today.replace(day=1)

        # Calculate next month start to find end of current month
        if j_today.month == 12:
            j_next_month = jdatetime.date(j_today.year + 1, 1, 1)
        else:
            j_next_month = jdatetime.date(j_today.year, j_today.month + 1, 1)

        days_in_month = (j_next_month - j_month_start).days

        # Greg start/end for DB queries
        g_start = j_month_start.togregorian()
        g_end = (j_next_month - timedelta(days=1)).togregorian()

        # Generate list of days (1..30/31)
        month_days = list(range(1, days_in_month + 1))

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

        # Fetch all completed tasks for this month that are habits
        completed_habit_tasks = Task.objects.filter(
            profile=profile,
            is_habit=True,
            is_completed=True,
            completed_at__date__range=[g_start, g_end],
        )

        # Map completions: { habit_title: { date_str: True } }
        habit_completion_map = {}
        # Map daily counts: { date_str: count }
        daily_habit_counts_map = {}

        for t in completed_habit_tasks:
            c_date = t.completed_at.date()
            c_date_str = c_date.strftime("%Y-%m-%d")

            # For Grid
            if t.title not in habit_completion_map:
                habit_completion_map[t.title] = set()
            habit_completion_map[t.title].add(c_date_str)

            # For Bar Chart
            daily_habit_counts_map[c_date_str] = (
                daily_habit_counts_map.get(c_date_str, 0) + 1
            )

        # Build Grid Structure
        habit_grid = []
        for habit in habits:
            row = []
            title = habit.task.title
            completed_dates = habit_completion_map.get(title, set())

            for d in range(days_in_month):
                c_j_date = j_month_start + timedelta(days=d)
                c_g_date_str = c_j_date.togregorian().strftime("%Y-%m-%d")
                is_done = c_g_date_str in completed_dates
                row.append(is_done)

            habit_grid.append({"title": title, "status": row})

        # Build Count Chart Data
        habit_counts_data = []
        for d in range(days_in_month):
            c_j_date = j_month_start + timedelta(days=d)
            c_g_date_str = c_j_date.togregorian().strftime("%Y-%m-%d")
            habit_counts_data.append(daily_habit_counts_map.get(c_g_date_str, 0))

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
            }
        )

        # 5. Inject Calendar Data (Existing Service)
        calendar_data = get_jalali_calendar_context(user)
        context.update(calendar_data)

        return context
