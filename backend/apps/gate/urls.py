from django.urls import path

from apps.gate import views

app_name = "gate"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("gate/", views.gate_view, name="gate"),
    path(
        "habit/toggle/<int:habit_id>/<str:date_str>/",
        views.toggle_habit_log,
        name="toggle_habit_log",
    ),
]
