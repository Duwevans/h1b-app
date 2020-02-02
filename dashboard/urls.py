from django.urls import path, include
from . import views
from dashboard.dash_apps.finished_apps import h1b_salary

urlpatterns = [
    path('', views.h1b_salary_dashboard, name='h1b_salary_dashboard'),
    path('about/', views.about, name='dashboards_about'),
    path('salaries/', views.h1b_salary_dashboard, name='h1b_salary_dashboard'),
    path('', include('django_plotly_dash.urls')),

]
