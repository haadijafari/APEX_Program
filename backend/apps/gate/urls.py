from django.urls import path, re_path

from apps.gate import views
from apps.gate.views import assets

app_name = "gate"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("gate/", views.gate_view, name="gate"),
    path("gate/autosave/", views.autosave_daily_entry, name="autosave_daily_entry"),
    re_path(
        r"^gate/(?P<date_str>\d{4}-\d{1,2}-\d{1,2})/$",
        views.gate_view,
        name="gate_date",
    ),
    path(
        "habit/toggle/<int:task_id>/<str:date_str>/",
        views.toggle_habit_log,
        name="toggle_habit_log",
    ),
    path(
        "routine/toggle/<int:task_id>/",
        views.toggle_task_log,
        name="toggle_routine_log",
    ),
    path("assets/emoji-data.json", assets.emoji_data_view, name="emoji_data"),
]
