import jdatetime
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.gate.forms import (
    DailyEntryForm,
    NegativeHighlightFormSet,
    PositiveHighlightFormSet,
)
from apps.gate.models import DailyEntry, DailyHighlight
from apps.tasks.models import Task, TaskLog


def get_date_context():
    """Returns today's date and its Jalali string representation."""
    today = timezone.now().date()
    j_date = jdatetime.date.fromgregorian(date=today)
    jalali_date_str = j_date.strftime("%A, %d %B %Y")
    return today, jalali_date_str


def get_or_create_daily_entry(user, date):
    """Gets or creates the DailyEntry for the given user and date."""
    entry, _ = DailyEntry.objects.get_or_create(user=user, date=date)
    return entry


def initialize_forms(daily_entry, post_data=None):
    """
    Initializes the Main Form and both Highlight Formsets.
    Handles both GET (empty/bound to instance) and POST (bound to data).
    """
    form = DailyEntryForm(post_data, instance=daily_entry)

    # specific querysets to separate positive/negative in the UI
    pos_qs = daily_entry.highlights.filter(category=DailyHighlight.Category.POSITIVE)
    neg_qs = daily_entry.highlights.filter(category=DailyHighlight.Category.NEGATIVE)

    pos_formset = PositiveHighlightFormSet(
        post_data,
        instance=daily_entry,
        queryset=pos_qs,
        prefix="pos",
        initial=[{"category": DailyHighlight.Category.POSITIVE}],
    )
    neg_formset = NegativeHighlightFormSet(
        post_data,
        instance=daily_entry,
        queryset=neg_qs,
        prefix="neg",
        initial=[{"category": DailyHighlight.Category.NEGATIVE}],
    )

    return {
        "form": form,
        "pos_formset": pos_formset,
        "neg_formset": neg_formset,
    }


def get_tasks_context(user, today):
    """
    Fetches tasks, splits them into Routines/Standalone,
    and identifies which are completed today.
    """
    # 1. Fetch Top-Level Tasks
    all_tasks = (
        Task.objects.filter(profile__user=user, is_active=True, parent__isnull=True)
        .prefetch_related("subtasks")
        .select_related("schedule")
        .annotate(subtask_count=Count("subtasks"))
        .order_by("order", "created_at")
    )

    # 2. Split into Routines and Standalone Tasks
    routines = [t for t in all_tasks if t.is_routine]
    standalone_tasks = [t for t in all_tasks if not t.is_routine]

    # 3. Fetch Completed Items for TODAY
    completed_task_ids = set(
        TaskLog.objects.filter(
            task__profile__user=user, completed_at__date=today
        ).values_list("task_id", flat=True)
    )

    return {
        "routines": routines,
        "tasks": standalone_tasks,
        "completed_task_ids": completed_task_ids,
    }


def process_autosave(user, post_data):
    """
    Handles validation and saving of the DailyEntry and its Highlights.
    Returns a dict with status and optional errors.
    """
    today = timezone.now().date()
    daily_entry = get_or_create_daily_entry(user, today)

    # Use helper to init forms with POST data
    forms = initialize_forms(daily_entry, post_data)
    form = forms["form"]
    pos_formset = forms["pos_formset"]
    neg_formset = forms["neg_formset"]

    if form.is_valid() and pos_formset.is_valid() and neg_formset.is_valid():
        form.save()
        _save_highlight_formset(pos_formset, DailyHighlight.Category.POSITIVE)
        _save_highlight_formset(neg_formset, DailyHighlight.Category.NEGATIVE)
        return {"success": True}
    else:
        return {
            "success": False,
            "errors": {
                "main": form.errors,
                "pos": pos_formset.errors,
                "neg": neg_formset.errors,
            },
        }


def _save_highlight_formset(formset, category):
    """Helper to save a highlight formset with a specific category."""
    instances = formset.save(commit=False)
    for obj in instances:
        obj.category = category
        obj.save()
    for obj in formset.deleted_objects:
        obj.delete()


def toggle_task_completion(user, task_id):
    """
    Toggles a Task's completion for today.
    Returns the new status ('added' or 'removed').
    """
    task = get_object_or_404(Task, id=task_id, profile__user=user)
    today = timezone.now().date()

    logs = TaskLog.objects.filter(task=task, completed_at__date=today)

    if logs.exists():
        logs.delete()
        return "removed"
    else:
        TaskLog.objects.create(task=task, completed_at=timezone.now())
        return "added"
