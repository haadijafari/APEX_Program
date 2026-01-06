import jdatetime
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.gate.forms import DayPageForm
from apps.gate.models.daily_entry import DayPage
from apps.tasks.models import Task, TaskLog


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

    # 1. Fetch Top-Level Tasks (Routines & Standalone Tasks)
    tasks = (
        Task.objects.filter(
            profile__user=request.user, is_active=True, parent__isnull=True
        )
        .prefetch_related("subtasks")
        .select_related("schedule")
        .order_by("order", "created_at")
    )

    # 2. Fetch Completed Items for TODAY
    # We fetch ALL logs for this user today (Parents AND Children)
    completed_task_ids = set(
        TaskLog.objects.filter(
            task__profile__user=request.user, completed_at__date=today
        ).values_list("task_id", flat=True)
    )

    context = {
        "day_page": day_page,
        "form": form,
        "tasks": tasks,
        "completed_task_ids": completed_task_ids,
        "today": today,
        "jalali_date_str": jalali_date_str,
    }
    return render(request, "gate/gate.html", context)


@login_required
@require_POST
def toggle_task_log(request, task_id):
    """
    AJAX Endpoint: Toggles a Task's completion for today.
    Works for both Parent Tasks (Routines) and Subtasks (Items).
    """
    # Verify ownership via profile
    task = get_object_or_404(Task, id=task_id, profile__user=request.user)
    today = timezone.now().date()

    # Check for existing log today
    log = TaskLog.objects.filter(task=task, completed_at__date=today).first()

    if log:
        log.delete()
        status = "removed"
    else:
        # Create Log with XP Snapshot
        TaskLog.objects.create(
            task=task, completed_at=timezone.now(), xp_earned=task.xp_reward
        )
        status = "added"

    return JsonResponse({"status": status, "task_id": task_id})
