from datetime import datetime

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
from apps.tasks.forms import GateTaskForm
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
    daily_entry_form = DailyEntryForm(post_data, instance=daily_entry)

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

    task_form = GateTaskForm()

    return {
        "form": daily_entry_form,
        "pos_formset": pos_formset,
        "neg_formset": neg_formset,
        "task_form": task_form,
    }


def create_standalone_task(user, data):
    """
    Validates and creates a new standalone task for the user.
    Returns (success: bool, result: Task|Errors).
    """
    form = GateTaskForm(data)
    if form.is_valid():
        task = form.save(commit=False)
        task.profile = user.profile
        # Standalone tasks have no parent or schedule by definition here
        task.save()
        return True, task
    return False, form.errors


def archive_task(user, task_id):
    """
    Soft-deletes a task (sets is_active=False).
    """
    # specific queryset to ensure user owns the task
    task = get_object_or_404(Task, id=task_id, profile__user=user)
    task.is_active = False
    task.save()
    return True


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

    # 2. Split into Categories
    # Routines: Tasks that are containers (have subtasks) AND have a schedule.
    routines = [t for t in all_tasks if t.is_routine]

    # Standalone Tasks: One-time tasks only (No Schedule).
    standalone_tasks = [t for t in all_tasks if not t.is_habit]

    # 3. Fetch Completed Items for TODAY
    completed_today_ids = set(
        TaskLog.objects.filter(
            task__profile__user=user, completed_at__date=today
        ).values_list("task_id", flat=True)
    )

    # 4. Filter Standalone Tasks (Pending vs Done Today vs Done Previously)
    # We want to hide One-Time tasks that were completed in the past.

    # Get IDs of standalone tasks that have EVER been completed
    st_ids = [t.id for t in standalone_tasks]
    ever_completed_ids = set(
        TaskLog.objects.filter(task_id__in=st_ids).values_list("task_id", flat=True)
    )

    pending_tasks = []
    done_tasks = []

    for t in standalone_tasks:
        if t.id in completed_today_ids:
            # Completed TODAY -> Show in Done List
            done_tasks.append(t)
        elif t.id not in ever_completed_ids:
            # Never completed -> Show in Pending List
            # (If it was completed yesterday, it's in ever_completed_ids but not completed_today_ids, so we skip it)
            pending_tasks.append(t)

    return {
        "routines": routines,
        "tasks": pending_tasks,  # Replaces the full list with just pending
        "done_tasks": done_tasks,  # New list for today's completions
        "completed_task_ids": completed_today_ids,
    }


def process_autosave(user, post_data):
    """
    Handles validation and saving of the DailyEntry and its Highlights.
    Returns a dict with status and optional errors.
    """
    # Date Handling: Default to today if not provided
    target_date = timezone.now().date()
    if date_str := post_data.get("date"):
        try:
            # Parse "2025-01-30" -> date object
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            pass  # Keep default (today) if parse fails

    # Fetch or Create the DailyEntry for the target date
    daily_entry = get_or_create_daily_entry(user, target_date)

    # Use helper to init forms with POST data
    forms = initialize_forms(daily_entry, post_data)
    form = forms["form"]
    pos_formset = forms["pos_formset"]
    neg_formset = forms["neg_formset"]

    if form.is_valid() and pos_formset.is_valid() and neg_formset.is_valid():
        form.save()
        pos_map = _save_highlight_formset(pos_formset, DailyHighlight.Category.POSITIVE)
        neg_map = _save_highlight_formset(neg_formset, DailyHighlight.Category.NEGATIVE)

        new_ids = {**pos_map, **neg_map}

        return {"success": True, "new_ids": new_ids}
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

    # Map form field names to their database IDs
    saved_map = {}
    for form in formset.forms:
        # If the instance exists (was created or updated) and has an ID
        if form.instance.pk:
            # form.add_prefix('id') generates the HTML name, e.g., 'pos-0-id'
            saved_map[form.add_prefix("id")] = form.instance.pk

    return saved_map


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
