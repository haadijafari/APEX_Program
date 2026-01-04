import jdatetime
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.gate.forms import DayPageForm
from apps.gate.models.daily_entry import DayPage
from apps.tasks.models import Routine, RoutineItem, RoutineLog


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

    # 1. Fetch Routines
    routines = Routine.objects.filter(
        profile__user=request.user, is_active=True
    ).prefetch_related("items__task")  # Prefetch items and their tasks

    # 2. Fetch Completed Items for TODAY
    # We get a set of IDs for all items logged today
    completed_item_ids = set(
        RoutineLog.objects.filter(
            item__routine__in=routines, completed_at__date=today
        ).values_list("item_id", flat=True)
    )

    context = {
        "day_page": day_page,
        "form": form,
        "routines": routines,
        "completed_item_ids": completed_item_ids,
        "today": today,
        "jalali_date_str": jalali_date_str,
    }
    return render(request, "gate/gate.html", context)


@login_required
@require_POST
def toggle_routine_log(request, item_id):
    """
    AJAX Endpoint: Toggles a routine item's completion for today.
    """
    # Verify ownership via profile
    item = get_object_or_404(
        RoutineItem, id=item_id, routine__profile__user=request.user
    )
    today = timezone.now().date()

    # Check for existing log today
    log = RoutineLog.objects.filter(item=item, completed_at__date=today).first()

    if log:
        log.delete()
        status = "removed"
    else:
        RoutineLog.objects.create(
            item=item,
            routine=item.routine,
            completed_at=timezone.now(),
        )
        status = "added"

    return JsonResponse({"status": status, "item_id": item_id})
