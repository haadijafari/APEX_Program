from django.urls import path
from apps.daily import views

app_name = 'daily'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('gate/', views.gate_view, name='gate'),
]
