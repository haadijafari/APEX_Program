from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from apps.gate.services import gate as gate_service


@login_required
def gate_view(request):
    """
    The 'Gate'.
    Where the Hunter enters to complete daily missions.
    Handles the DailyEntry form and Routine display.
    """
    # 1. Date & Entry Setup
    today, jalali_date_str = gate_service.get_date_context()
    daily_entry = gate_service.get_or_create_daily_entry(request.user, today)

    # 2. Forms & Data
    forms_context = gate_service.initialize_forms(daily_entry)
    tasks_context = gate_service.get_tasks_context(request.user, today)

    context = {
        "daily_entry": daily_entry,
        "today": today,
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
