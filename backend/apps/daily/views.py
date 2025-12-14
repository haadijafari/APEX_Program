from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from apps.daily.models.model_daypage import DayPage
from .models.model_routine import Routine
from .forms import DayPageForm

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
