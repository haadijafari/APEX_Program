from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required

from apps.daily.models.model_daypage import DayPage
from apps.daily.models.model_routine import Routine
from apps.daily.forms import DayPageForm

@login_required
def gate_view(request):
    """
    The 'Gate'.
    Where the Hunter enters to complete daily missions.
    Handles the DayPage form and Routine display.
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
            return redirect('daily:gate')
    else:
        form = DayPageForm(instance=day_page)

    # Fetch Routines (for display)
    routines = Routine.objects.filter(
        user=request.user, 
        is_active=True
    ).prefetch_related('routine_items')

    context = {
        'day_page': day_page,
        'form': form,
        'routines': routines,
        'today': today,
    }
    return render(request, 'daily/gate.html', context)
