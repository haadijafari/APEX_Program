# backend/apps/gate/services/index.py
from datetime import datetime, timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.gate.models import DailyEntry
from apps.profiles.models import PlayerProfile
from apps.tasks.models import Task, TaskLog


def get_player_stats(user):
    """
    Fetches the user's profile and formats stats for the radar chart.
    """
    profile, _ = PlayerProfile.objects.get_or_create(user=user)
    stats = getattr(profile, "stats", None)

    if stats:
        # Match order: ["STR", "INT", "CHA", "WIL", "WIS"]
        values = [
            stats.str_level,
            stats.int_level,
            stats.cha_level,
            stats.wil_level,
            stats.wis_level,
        ]
    else:
        values = [1, 1, 1, 1, 1]

    return {
        "profile": profile,
        "stat_labels": ["STR", "INT", "CHA", "WIL", "WIS"],
        "stat_values": values,
    }


def get_sleep_data(user, month_info):
    """
    Calculates sleep duration for every day in the current month.
    Returns a list of floats representing hours.
    """
    days_in_month = month_info["days_in_month"]
    j_month_start = month_info["j_month_start"]
    g_start = month_info["g_start"]
    g_end = month_info["g_end"]

    # Fetch entries in bulk
    daily_entries = DailyEntry.objects.filter(user=user, date__range=[g_start, g_end])
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

    return sleep_data


def get_habit_grid_context(user, profile, month_info):
    """
    Builds the Habit Grid, Daily Counts, and Chart Data.
    """
    today = timezone.now().date()
    days_in_month = month_info["days_in_month"]
    j_month_start = month_info["j_month_start"]
    j_today = month_info["j_today"]
    g_start = month_info["g_start"]
    g_end = month_info["g_end"]

    # 1. Fetch Habits & Logs
    habits = Task.objects.filter(
        profile=profile,
        is_active=True,
        schedule__isnull=False,
    ).select_related("schedule")

    habit_logs = TaskLog.objects.filter(
        task__in=habits,
        completed_at__date__range=[g_start, g_end],
    ).select_related("task")

    # 2. Map Data
    habit_completion_map = set()
    daily_habit_counts_map = {}
    daily_habit_titles_map = {}

    for log in habit_logs:
        c_date = log.completed_at.date()
        c_date_str = c_date.strftime("%Y-%m-%d")

        habit_completion_map.add((log.task.id, c_date_str))

        daily_habit_counts_map[c_date_str] = (
            daily_habit_counts_map.get(c_date_str, 0) + 1
        )
        if c_date_str not in daily_habit_titles_map:
            daily_habit_titles_map[c_date_str] = []
        daily_habit_titles_map[c_date_str].append(log.task.title)

    # 3. Build Grid Rows
    habit_grid = []
    for habit in habits:
        row = []
        start_date = (
            habit.schedule.start_time.date() if habit.schedule.start_time else None
        )

        for d in range(days_in_month):
            c_j_date = j_month_start + timedelta(days=d)
            c_g_date = c_j_date.togregorian()
            c_g_date_str = c_g_date.strftime("%Y-%m-%d")

            is_done = (habit.id, c_g_date_str) in habit_completion_map
            is_today = c_j_date == j_today

            # Coloring State
            state = "future"
            if is_done:
                state = "completed"
            elif c_g_date == today:
                state = "today"
            elif c_g_date < today:
                if start_date and c_g_date < start_date:
                    state = "before-start"
                else:
                    state = "missed"

            row.append(
                {
                    "date": c_g_date_str,
                    "status": is_done,
                    "state": state,
                    "is_today": is_today,
                }
            )

        habit_grid.append({"id": habit.id, "title": habit.title, "status": row})

    # 4. Build Chart Data
    habit_counts_data = []
    habit_titles_data = []
    for d in range(days_in_month):
        c_j_date = j_month_start + timedelta(days=d)
        c_g_date_str = c_j_date.togregorian().strftime("%Y-%m-%d")

        habit_counts_data.append(daily_habit_counts_map.get(c_g_date_str, 0))
        habit_titles_data.append(daily_habit_titles_map.get(c_g_date_str, []))

    return {
        "habit_grid": habit_grid,
        "habit_counts_data": habit_counts_data,
        "habit_titles_data": habit_titles_data,
        "total_active_habits": habits.count(),
    }


def perform_habit_toggle(user, task_id, date_str):
    """
    Toggles a habit log.
    Returns a dictionary of updated stats/icons for the frontend.
    """
    profile = PlayerProfile.objects.filter(user=user).first()
    if not profile:
        raise ValueError("Profile not found")

    task = get_object_or_404(
        Task.objects.select_related("schedule"), id=task_id, profile=profile
    )

    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Invalid date format")

    # 1. Toggle Logic
    logs = TaskLog.objects.filter(task=task, completed_at__date=date_obj)

    if logs.exists():
        logs.delete()
        status = "removed"
    else:
        now = timezone.now()
        if date_obj == now.date():
            log_time = now
        else:
            # Mid-day to avoid timezone edge cases
            dt_naive = datetime.combine(date_obj, datetime.min.time().replace(hour=12))
            log_time = timezone.make_aware(dt_naive)

        TaskLog.objects.create(task=task, completed_at=log_time)
        status = "added"

    # 2. Refresh Stats
    profile.refresh_from_db()
    stats = profile.stats

    xp_percent = 0
    if profile.xp_required > 0:
        xp_percent = (profile.xp_current / profile.xp_required) * 100

    new_stats_values = [
        stats.str_level,
        stats.int_level,
        stats.cha_level,
        stats.wil_level,
        stats.wis_level,
    ]

    # 3. Icon Logic (Presentation Helper)
    icon_html = _get_status_icon_html(status, date_obj, task)

    # 4. Daily Count Calculation
    habits = Task.objects.filter(
        profile=profile, is_active=True, schedule__isnull=False
    )
    updated_logs = TaskLog.objects.filter(
        task__in=habits, completed_at__date=date_obj
    ).select_related("task")

    return {
        "status": status,
        "icon_html": icon_html,
        "date": date_str,
        "task_id": task_id,
        "daily_count": updated_logs.count(),
        "daily_titles": [log.task.title for log in updated_logs],
        "new_level": profile.level,
        "new_xp_current": profile.xp_current,
        "new_xp_required": profile.xp_required,
        "new_xp_percent": round(xp_percent, 1),
        "new_stats": new_stats_values,
    }


def _get_status_icon_html(status, date_obj, task):
    """Helper to determine the HTML icon for the grid cell."""
    if status == "added":
        return '<span class="fs-6">✅</span>'

    today = timezone.now().date()
    start_date = None
    if task.schedule and task.schedule.start_time:
        start_date = task.schedule.start_time.date()

    if date_obj == today:
        return '<span class="text-warning">●</span>'
    elif date_obj > today:
        return '<span class="text-secondary opacity-25">·</span>'
    else:
        # Past
        if start_date and date_obj < start_date:
            return '<span class="text-secondary opacity-25">·</span>'
        else:
            return '<span class="text-danger opacity-50">✕</span>'
