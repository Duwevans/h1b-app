from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return render(request, 'dashboard/home.html')

def about(request):
    return render(request, 'dashboard/about.html')

def h1b_salary_dashboard(request):
    return render(request, 'dashboard/h1b_data.html')
