from django.shortcuts import render

from website.content import get_home_context


def home(request):
    return render(request, 'website/home.html', get_home_context(request))
