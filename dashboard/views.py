from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def placeholder_dashboard(request):
    """
    Placeholder dashboard view.
    Will be replaced with actual dashboard implementation in task 14.
    """
    return render(request, 'dashboard/placeholder.html', {
        'user': request.user
    })
