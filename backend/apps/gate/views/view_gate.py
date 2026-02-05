import jdatetime
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.gate.services import gate as gate_service


@login_required
def gate_view(request, date_str=None):
    """
    The 'Gate'.
    Where the Hunter enters to complete daily missions.
    Handles the DailyEntry form and Routine display.
    """
    if date_str:
        try:
            # 1. Parse Jalali Date from URL (e.g. "1403-11-10")
            j_year, j_month, j_day = map(int, date_str.split("-"))
            j_date = jdatetime.date(j_year, j_month, j_day)

            # 2. Convert to Gregorian for System Logic
            target_date = j_date.togregorian()

            # 3. Format Display String
            jalali_date_str = j_date.strftime("%A %d %B %Y")
        except (ValueError, TypeError):
            # Fallback to today if date is invalid
            return HttpResponseRedirect(reverse("gate:gate"))
    else:
        # Default: Use Today
        target_date, jalali_date_str = gate_service.get_date_context()

    # Get or Create the Entry for the TARGET date (not necessarily today)
    daily_entry = gate_service.get_or_create_daily_entry(request.user, target_date)

    # Forms & Data
    forms_context = gate_service.initialize_forms(daily_entry)
    tasks_context = gate_service.get_tasks_context(request.user, target_date)

    context = {
        "daily_entry": daily_entry,
        "today": target_date,
        "jalali_date_str": jalali_date_str,
        **forms_context,
        **tasks_context,
    }
    return render(request, "gate/gate.html", context)


@login_required
@require_POST
def autosave_daily_entry(request):
    """
    AJAX Endpoint: Auto-saves the DailyEntry form fields.
    """
    result = gate_service.process_autosave(request.user, request.POST)

    if result["success"]:
        return JsonResponse({"status": "success", "new_ids": result.get("new_ids", {})})

    return JsonResponse({"status": "error", "errors": result["errors"]}, status=400)


@login_required
@require_POST
def toggle_task_log(request, task_id):
    """
    AJAX Endpoint: Toggles a Task's completion for today.
    """
    status = gate_service.toggle_task_completion(request.user, task_id)
    return JsonResponse({"status": status, "task_id": task_id})


@login_required
@require_POST
def add_task_view(request):
    """
    AJAX Endpoint: Creates a new task via Modal.
    """
    success, result = gate_service.create_standalone_task(request.user, request.POST)

    if success:
        # Return data needed to prepend the new task to the list without refresh
        return JsonResponse(
            {
                "status": "success",
                "task": {
                    "id": result.id,
                    "title": result.title,
                    "rank": result.final_rank,
                    "description": result.description,
                },
            }
        )

    return JsonResponse({"status": "error", "errors": result}, status=400)


@login_required
def task_details_view(request, task_id):
    """
    AJAX Endpoint: Returns task details (JSON) for editing.
    """
    data = gate_service.get_task_details(request.user, task_id)
    return JsonResponse({"status": "success", "task": data})


@login_required
@require_POST
def update_task_view(request, task_id):
    """
    AJAX Endpoint: Updates an existing task.
    """
    success, result = gate_service.update_standalone_task(
        request.user, task_id, request.POST
    )

    if success:
        return JsonResponse(
            {
                "status": "success",
                "task": {
                    "id": result.id,
                    "title": result.title,
                    "rank": result.computed_rank,
                    "description": result.description,
                },
            }
        )

    return JsonResponse({"status": "error", "errors": result}, status=400)


@login_required
@require_POST
def archive_task_view(request, task_id):
    """
    AJAX Endpoint: Soft deletes a task.
    """
    gate_service.archive_task(request.user, task_id)
    return JsonResponse({"status": "success", "task_id": task_id})
