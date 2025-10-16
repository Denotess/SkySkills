from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    return render(request, "skills/index.html")

def skill_list(request):
    context = {
        'skills': ['Mining', 'Farming', 'Fishing', 'Combat']
    }
    return render(request, 'skills/skill_list.html', context)
