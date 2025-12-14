from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from apps.daily.models.model_daypage import DayPage
import jdatetime
from datetime import timedelta

from .models.model_routine import Routine
from .forms import DayPageForm
from auths.user.models import PlayerProfile

@login_required
def daily_dashboard(request):
    """
    The main command center. 
    1. Fetches (or creates) the DayPage for TODAY.
    2. Fetches all active Routines (Morning/Night).
    3. Handles saving the DayPage form.
    """
    today = timezone.now().date()
    
    # Get or Create the page for today
    day_page, created = DayPage.objects.get_or_create(
        user=request.user,
        date=today
    )

    # Handle Form Submission (Saving the DayPage data)
    if request.method == 'POST':
        form = DayPageForm(request.POST, instance=day_page)
        if form.is_valid():
            form.save()
            return redirect('daily:dashboard') # Refresh to show saved data
    else:
        form = DayPageForm(instance=day_page)

    # Fetch Routines (for display)
    routines = Routine.objects.filter(user=request.user, is_active=True).prefetch_related('routine_items')

    context = {
        'day_page': day_page,
        'form': form,
        'routines': routines,
        'today': today,
    }
    return render(request, 'daily/dashboard.html', context)

@login_required
def index(request):
    """
    The 'Status Window' (Main Home Page).
    Fetches real player stats from the database.
    """
    j_today = jdatetime.date.today()
    today = timezone.now().date()
    has_daily_log = DayPage.objects.filter(user=request.user, date=today).exists()
    
    # ----- Player Stats Logic -----
    # Get the profile safely (create it if it doesn't exist for old users)
    profile, created = PlayerProfile.objects.get_or_create(user=request.user)
    # Fetch all attributes for the chart
    attributes = request.user.attributes.all()
    # Calculate Streak (Simple version: Count total DayPages)
    # TODO: Make this 'consecutive days'
    streak_count = DayPage.objects.filter(user=request.user).count()
    # Prepare data for Chart.js
    # We need two lists: labels (names) and data (values)
    stat_labels = [attr.name for attr in attributes] 
    stat_values = [attr.value for attr in attributes]


    # ----- Calendar Logic -----
    # Get the first day of the current Jalali month
    first_day_of_month = j_today.replace(day=1)
    
    # Find out which day of the week the month starts on (0=Sat, 1=Sun, ... 6=Fri for Jalali)
    # jdatetime.weekday(): 0=Sat, 1=Sun, ..., 6=Fri
    start_weekday = first_day_of_month.weekday() 
    
    # Generate the days
    calendar_days = []

    # Add empty slots for days before the 1st of the month
    for i in range(start_weekday):
        calendar_days.append(None)
        
    # Add the actual days of the month
    # Jalali months: first 6 are 31 days, next 5 are 30, last is 29/30
    if j_today.month == 12:
        # If it's Esfand (12th month), next month is Farvardin (1st) of next year
        next_month_start = jdatetime.date(j_today.year + 1, 1, 1)
    else:
        # Otherwise, just add 1 to the month
        next_month_start = jdatetime.date(j_today.year, j_today.month + 1, 1)

    # 3. Calculate the difference in days (Automatic & Accurate)
    month_length = (next_month_start - first_day_of_month).days

    for day in range(1, month_length + 1):
        date_obj = first_day_of_month + timedelta(days=day-1)
        is_today = (date_obj == j_today)
        
        # Check if a log exists for this specific day (for the heatmap color)
        # Note: We convert Jalali back to Gregorian for the DB query
        g_date = date_obj.togregorian()
        has_log = DayPage.objects.filter(user=request.user, date=g_date).exists()
        
        calendar_days.append({
            'day': day,
            'is_today': is_today,
            'has_log': has_log,
            'full_date': date_obj.strftime("%Y-%m-%d")
        })

    context = {
        "today": today,
        "j_today": j_today,
        "calendar_days": calendar_days,
        "has_daily_log": has_daily_log,
        "profile": profile,
        "stat_labels": stat_labels,
        "stat_values": stat_values,
        "streak": streak_count,
    }
    return render(request, 'daily/index.html', context)
