import jdatetime
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.gate.forms import (
    DailyEntryForm,
    NegativeHighlightFormSet,
    PositiveHighlightFormSet,
)
from apps.gate.models import DailyEntry, DailyHighlight
from apps.tasks.models import Task, TaskLog


@login_required
def gate_view(request):
    """
    The 'Gate'.
    Where the Hunter enters to complete daily missions.
    Handles the DailyEntry form and Routine display.
    """
    today = timezone.now().date()
    j_date = jdatetime.date.fromgregorian(date=today)
    jalali_date_str = j_date.strftime("%A, %d %B %Y")

    # Get or Create the page for today
    daily_entry, created = DailyEntry.objects.get_or_create(
        user=request.user, date=today
    )

    # Note: Traditional POST handling removed in favor of Auto-Save.
    form = DailyEntryForm(instance=daily_entry)

    # Initialize Formsets with specific querysets to separate them
    pos_qs = daily_entry.highlights.filter(category=DailyHighlight.Category.POSITIVE)
    neg_qs = daily_entry.highlights.filter(category=DailyHighlight.Category.NEGATIVE)

    pos_formset = PositiveHighlightFormSet(
        instance=daily_entry,
        queryset=pos_qs,
        prefix="pos",
        initial=[{"category": DailyHighlight.Category.POSITIVE}],
    )
    neg_formset = NegativeHighlightFormSet(
        instance=daily_entry,
        queryset=neg_qs,
        prefix="neg",
        initial=[{"category": DailyHighlight.Category.NEGATIVE}],
    )

    # 1. Fetch Top-Level Tasks
    # OPTIMIZATION: Annotate subtask_count so 'is_routine' doesn't hit DB
    all_tasks = (
        Task.objects.filter(
            profile__user=request.user, is_active=True, parent__isnull=True
        )
        .prefetch_related("subtasks")
        .select_related("schedule")
        .annotate(subtask_count=Count("subtasks"))
        .order_by("order", "created_at")
    )

    # 2. Split into Routines and Standalone Tasks
    # This allows the template to use {% empty %} correctly
    routines = [t for t in all_tasks if t.is_routine]
    standalone_tasks = [t for t in all_tasks if not t.is_routine]

    # 3. Fetch Completed Items for TODAY
    completed_task_ids = set(
        TaskLog.objects.filter(
            task__profile__user=request.user, completed_at__date=today
        ).values_list("task_id", flat=True)
    )

    context = {
        "daily_entry": daily_entry,
        "form": form,
        "pos_formset": pos_formset,
        "neg_formset": neg_formset,
        "routines": routines,
        "tasks": standalone_tasks,
        "completed_task_ids": completed_task_ids,
        "today": today,
        "jalali_date_str": jalali_date_str,
    }
    return render(request, "gate/gate.html", context)


@login_required
@require_POST
def autosave_daily_entry(request):
    """
    AJAX Endpoint: Auto-saves the DailyEntry form fields.
    """
    daily_entry, _ = DailyEntry.objects.get_or_create(
        user=request.user, date=timezone.now().date()
    )

    # 1. Main Form
    form = DailyEntryForm(request.POST, instance=daily_entry)

    # 2. Formsets
    pos_formset = PositiveHighlightFormSet(
        request.POST, instance=daily_entry, prefix="pos"
    )
    neg_formset = NegativeHighlightFormSet(
        request.POST, instance=daily_entry, prefix="neg"
    )

    if form.is_valid() and pos_formset.is_valid() and neg_formset.is_valid():
        form.save()

        # 1. Save Positives (Allow empty strings)
        instances_pos = pos_formset.save(commit=False)
        for obj in instances_pos:
            obj.category = DailyHighlight.Category.POSITIVE
            obj.save()
        # Explicitly delete objects marked for deletion
        for obj in pos_formset.deleted_objects:
            obj.delete()

        # 2. Save Improvements (Allow empty strings)
        instances_neg = neg_formset.save(commit=False)
        for obj in instances_neg:
            obj.category = DailyHighlight.Category.NEGATIVE
            obj.save()
        for obj in neg_formset.deleted_objects:
            obj.delete()

        return JsonResponse({"status": "success"})

    else:
        # Combine errors for debugging
        errors = {
            "main": form.errors,
            "pos": pos_formset.errors,
            "neg": neg_formset.errors,
        }
        return JsonResponse({"status": "error", "errors": errors}, status=400)


@login_required
@require_POST
def toggle_task_log(request, task_id):
    """
    AJAX Endpoint: Toggles a Task's completion for today.
    Works for both Parent Tasks (Routines) and Subtasks (Items).
    """
    task = get_object_or_404(Task, id=task_id, profile__user=request.user)
    today = timezone.now().date()

    # Check for existing log today
    logs = TaskLog.objects.filter(task=task, completed_at__date=today)

    if logs:
        logs.delete()
        status = "removed"
    else:
        TaskLog.objects.create(task=task, completed_at=timezone.now())
        status = "added"

    return JsonResponse({"status": status, "task_id": task_id})
