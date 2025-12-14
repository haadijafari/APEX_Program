import jdatetime
from datetime import timedelta
from apps.daily.models.model_daypage import DayPage


def get_jalali_calendar_context(user):
    """
    Generates the data structure for the Jalali calendar grid (Heatmap).
    Returns a dictionary ready to be merged into the view context.
    """
    j_today = jdatetime.date.today()
    # jdatetime handles the names correctly (e.g., "Azar", "Aban")
    current_month_str = j_today.strftime("%B %Y")
    
    # 1. Get the first day of the current Jalali month
    first_day_of_month = j_today.replace(day=1)
    
    # 2. Calculate days in month (handling year rollover)
    if j_today.month == 12:
        next_month_start = jdatetime.date(j_today.year + 1, 1, 1)
    else:
        next_month_start = jdatetime.date(j_today.year, j_today.month + 1, 1)
        
    month_length = (next_month_start - first_day_of_month).days

    # 3. Prepare the grid (Empty slots for start of week)
    # 0=Sat, 1=Sun, ..., 6=Fri
    start_weekday = first_day_of_month.weekday() 
    calendar_days = [None] * start_weekday

    # 4. Fill in the actual days
    for day in range(1, month_length + 1):
        date_obj = first_day_of_month + timedelta(days=day-1)
        
        # Check database for log (Heatmap logic)
        g_date = date_obj.togregorian()
        has_log = DayPage.objects.filter(user=user, date=g_date).exists()
        
        calendar_days.append({
            'day': day,
            'is_today': (date_obj == j_today),
            'has_log': has_log,
            'full_date': date_obj.strftime("%Y-%m-%d")
        })

    return {
        "j_today": j_today,
        "current_month_str": current_month_str,
        "calendar_days": calendar_days,
    }
# TODO: Occasions and holidays should be shown.
# TODO: Add navigation for previous/next months.
