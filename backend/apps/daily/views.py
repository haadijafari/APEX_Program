from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from apps.daily.models.model_daypage import DayPage
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
    today = timezone.now().date()
    has_daily_log = DayPage.objects.filter(user=request.user, date=today).exists()
    
    # Get the profile safely (create it if it doesn't exist for old users)
    profile, created = PlayerProfile.objects.get_or_create(user=request.user)
    # Fetch all attributes for the chart
    attributes = request.user.attributes.all()

    # Prepare data for Chart.js
    # We need two lists: labels (names) and data (values)
    stat_labels = [attr.name for attr in attributes] 
    stat_values = [attr.value for attr in attributes]

    # Calculate Streak (Simple version: Count total DayPages)
    # Later we can make this 'consecutive days'
    streak_count = DayPage.objects.filter(user=request.user).count()

    context = {
        "today": today,
        "has_daily_log": has_daily_log,
        "profile": profile,
        "stat_labels": stat_labels,
        "stat_values": stat_values,
        "streak": streak_count,
    }
    return render(request, 'daily/index.html', context)
