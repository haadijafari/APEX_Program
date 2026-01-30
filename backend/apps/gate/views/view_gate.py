import jdatetime
from django.contrib.auth.decorators import login_required
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
        return JsonResponse({"status": "success"})

    return JsonResponse({"status": "error", "errors": result["errors"]}, status=400)


@login_required
@require_POST
def toggle_task_log(request, task_id):
    """
    AJAX Endpoint: Toggles a Task's completion for today.
    """
    status = gate_service.toggle_task_completion(request.user, task_id)
    return JsonResponse({"status": status, "task_id": task_id})
