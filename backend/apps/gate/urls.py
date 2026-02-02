from django.urls import path, re_path

from apps.gate import views
from apps.gate.views import assets

app_name = "gate"

urlpatterns = [
    # Home / Index View
    path("", views.IndexView.as_view(), name="index"),
    # Gate View
    path("gate/", views.gate_view, name="gate"),
    path("gate/autosave/", views.autosave_daily_entry, name="autosave_daily_entry"),
    re_path(
        r"^gate/(?P<date_str>\d{4}-\d{1,2}-\d{1,2})/$",
        views.gate_view,
        name="gate_date",
    ),
    # Toggle Logic
    path(
        "habit/toggle/<int:task_id>/<str:date_str>/",
        views.toggle_habit_log,
        name="toggle_habit_log",
    ),
    path(
        "task/toggle/<int:task_id>/",
        views.toggle_task_log,
        name="toggle_task_log",
    ),
    # Task Manager
    path("task/add/", views.add_task_view, name="add_task"),
    path("task/<int:task_id>/details/", views.task_details_view, name="task_details"),
    path("task/<int:task_id>/update/", views.update_task_view, name="update_task"),
    path("task/<int:task_id>/archive/", views.archive_task_view, name="archive_task"),
    # Assets
    path("assets/emoji-data.json", assets.emoji_data_view, name="emoji_data"),
]
