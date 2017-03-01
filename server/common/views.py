from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse


def hello(request):
    return render(request, 'base.html')
