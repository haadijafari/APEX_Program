from datetime import timedelta

import jdatetime

from apps.gate.models.daily_entry import DailyEntry


def get_current_month_info():
    """
    Calculates the boundaries and length of the current Jalali month.
    Returns a dict with Gregorian and Jalali details reusable by Views.
    """
    j_today = jdatetime.date.today()

    # 1. Get the first day of the current Jalali month
    j_month_start = j_today.replace(day=1)

    # 2. Calculate days in month (handling year rollover and leap years automatically)
    if j_today.month == 12:
        j_next_month = jdatetime.date(j_today.year + 1, 1, 1)
    else:
        j_next_month = jdatetime.date(j_today.year, j_today.month + 1, 1)

    days_in_month = (j_next_month - j_month_start).days

    # 3. Gregorian Boundaries for DB Queries
    g_start = j_month_start.togregorian()
    g_end = (j_next_month - timedelta(days=1)).togregorian()

    return {
        "j_today": j_today,
        "j_month_start": j_month_start,
        "days_in_month": days_in_month,
        "g_start": g_start,
        "g_end": g_end,
        "month_days": list(range(1, days_in_month + 1)),  # [1, 2, ... 30]
    }


def get_jalali_calendar_context(user):
    """
    Generates the data structure for the Jalali calendar grid (Heatmap).
    Returns a dictionary ready to be merged into the view context.
    """
    # Reuse the central logic
    month_info = get_current_month_info()

    j_today = month_info["j_today"]
    j_month_start = month_info["j_month_start"]
    days_in_month = month_info["days_in_month"]

    current_month_str = j_today.strftime("%B %Y")

    # Prepare the grid (Empty slots for start of week)
    # 0=Sat, 1=Sun, ..., 6=Fri
    start_weekday = j_month_start.weekday()
    calendar_days = [None] * start_weekday

    # Fill in the actual days
    for day in range(1, days_in_month + 1):
        date_obj = j_month_start + timedelta(days=day - 1)

        # Check database for log (Heatmap logic)
        g_date = date_obj.togregorian()
        has_log = DailyEntry.objects.filter(user=user, date=g_date).exists()

        calendar_days.append(
            {
                "day": day,
                "is_today": (date_obj == j_today),
                "is_past": (date_obj < j_today),
                "is_future": (date_obj > j_today),
                "has_log": has_log,
                "full_date": date_obj.strftime("%Y-%m-%d"),
            }
        )

    return {
        "j_today": j_today,
        "current_month_str": current_month_str,
        "calendar_days": calendar_days,
    }


# TODO: Occasions and holidays should be shown.
# TODO: Add navigation for previous/next months.
