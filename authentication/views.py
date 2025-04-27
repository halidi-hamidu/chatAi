from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate, get_user_model
from .forms import *
from .models import *
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse
from utils import *
from django.contrib import messages
from django.contrib.auth.models import User

def loginView(request):
    if request.method == "POST" and "login_btn" in request.POST:
        # form = AuthenticationForm(request.POST or None)
        username = request.POST.get("username")
        password = request.POST.get("password")

        get_user = User.objects.filter(username = username).first()
        authenticated_user = authenticate(request, username = username, password = password)
        if authenticated_user is None:
            messages.error(request, f"user does not exists")
            return redirect("authentication:loginView")
        else:
            login(request, authenticated_user)
            messages.success(request, f"Welcome {username}")
            return redirect("phishingDetector:homeView")

    form = AuthenticationForm()
    templates = "authentication/login.html"
    context = {
        "form":form
    }
    return render(request, templates, context)

def registerView(request):
    if request.method == "POST" and "register_btn" in request.POST:
        form = RegisterForm(request.POST or None)
        if form.is_valid():
            if not get_user_model().objects.filter(username = request.POST.get("username")).exists():
                form.save()
                messages.success(request, f"User was created successfully!, ask your admin for more authorization.")
                return redirect("authentication:registerView")
            messages.error(request, f"This user is already exist, try another user")
            return redirect("authentication:registerView")
        messages.info(request, f"Something went wrong, invalid credentials")
        return redirect("authentication:registerView")

    form = RegisterForm()
    templates = "authentication/register.html"
    context = {
        "form":form
    }
    return render(request, templates, context)

def logoutView(request):
    if request.method == "POST" and "logout_btn" in request.POST:
        logout(request)
        return redirect("authentication:loginView")

def get_user(request):
    response = supabase.table("account").select("*").execute()
    return JsonResponse(response.data, safe=False)
