import jdatetime
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.gate.forms import DayPageForm
from apps.gate.models.daily_entry import DayPage
from apps.tasks.models import Routine


@login_required
def gate_view(request):
    """
    The 'Gate'.
    Where the Hunter enters to complete daily missions.
    Handles the DayPage form and Routine display.
    """
    today = timezone.now().date()
    j_date = jdatetime.date.fromgregorian(date=today)
    jalali_date_str = j_date.strftime("%A, %d %B %Y")

    # Get or Create the page for today
    day_page, created = DayPage.objects.get_or_create(user=request.user, date=today)

    # Handle Form Submission (Saving the DayPage data)
    if request.method == "POST":
        form = DayPageForm(request.POST, instance=day_page)
        if form.is_valid():
            form.save()
            return redirect("gate:gate")
    else:
        form = DayPageForm(instance=day_page)

    # Fetch Routines (for display)
    routines = Routine.objects.filter(
        profile__user=request.user, is_active=True
    ).prefetch_related("items")

    context = {
        "day_page": day_page,
        "form": form,
        "routines": routines,
        "today": today,
        "jalali_date_str": jalali_date_str,
    }
    return render(request, "gate/gate.html", context)
