from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.shortcuts import render


@require_GET
def health_check(request):
    """Health check endpoint for monitoring."""
    return JsonResponse({
        "status": "ok",
        "service": "skyskills-fishing",
        "version": "0.1.0"
    })


def home(request):
    """Homepage with IGN input form."""
    return render(request, 'home.html')
