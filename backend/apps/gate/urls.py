from django.urls import path

from apps.gate import views

app_name = "gate"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("gate/", views.gate_view, name="gate"),
]
