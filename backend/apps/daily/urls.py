from django.urls import path
from . import views

app_name = 'daily'

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.daily_dashboard, name='dashboard'),
]
