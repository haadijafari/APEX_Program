from django.urls import path
from . import views

app_name = 'daily'

urlpatterns = [
    path('dashboard/', views.daily_dashboard, name='dashboard'),
    # Add a redirect from root if you want:
    # path('', views.daily_dashboard, name='home'), 
]
