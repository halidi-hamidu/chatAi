from django.shortcuts import render, redirect, get_object_or_404
from utils import *
from django.http import JsonResponse
import json
from django.views.decorators.cache import cache_control
from django.contrib.auth.decorators import login_required
from authentication.forms import *
from django.contrib.auth import get_user_model
from django.contrib import messages
from authentication.models import *

# Create your views here.
@cache_control(no_cache = True, privacy = True, must_revalidate = True, no_store = True)
@login_required(login_url="/authentication/loginView")
def homeView(request):
    response_chats = supabase.table("chats").select("*").execute()
    response_chats_members = supabase.table("chats").select("chat_members").execute()
    response_account = supabase.table("account").select("*").execute()
    response_messages = supabase.table("messages").select("*").execute()
    chats = response_chats.data
    messages = response_messages.data
    accounts = response_account.data
    chat_members = response_chats_members.data
    get_total_chats = len(chats)
    get_total_messages = len(messages)
    templates = "phishingDetector/home.html"
    context = {
        "chats":chats,
        "get_total_chats":get_total_chats,
        "get_total_messages":get_total_messages,
        "chat_members":chat_members,
        "accounts":accounts
    }
    return render(request, templates, context)

@cache_control(no_cache = True, privacy = True, must_revalidate = True, no_store = True)
@login_required(login_url="/authentication/loginView")
def chatsView(request):
    response_chats = supabase.table("chats").select("*").execute()
    response_account = supabase.table("account").select("*").execute()
    accounts = response_account.data
    chats = response_chats.data
    templates = "phishingDetector/chats.html"
    context = {
        "chats":chats,
        "accounts":accounts
    }
    return render(request, templates, context)

@cache_control(no_cache = True, privacy = True, must_revalidate = True, no_store = True)
@login_required(login_url="/authentication/loginView")
def messagesView(request):
    response_messages = supabase.table("messages").select("*").execute()
    response_account = supabase.table("account").select("*").execute()
    response_chats = supabase.table("chats").select("*").execute()
    chats = response_chats.data
    accounts = response_account.data
    chat_messages = response_messages.data
    templates = "phishingDetector/messages.html"
    context = {
        "chat_messages":chat_messages,
        "accounts":accounts,
        "chats":chats
    }
    return render(request, templates, context)

@cache_control(no_cache = True, privacy = True, must_revalidate = True, no_store = True)
@login_required(login_url="/authentication/loginView")
def settingsView(request):
    users = get_user_model().objects.all()
    form = AuthorizationForm()
    templates = "phishingDetector/settings.html"
    context = {
        "form":form,
        "users":users
    }
    return render(request, templates, context)

@cache_control(no_cache = True, privacy = True, must_revalidate = True, no_store = True)
@login_required(login_url="/authentication/loginView")
def settingsDeleteView(request, user_id):
    if request.method == "POST" and "delete_user_btn" in request.POST:
        user = get_user_model().objects.filter(pk = user_id).first()
        user.delete()
        messages.success(request, f"user was deleted successfully!")
        return redirect("phishingDetector:settingsView")

@cache_control(no_cache = True, privacy = True, must_revalidate = True, no_store = True)
@login_required(login_url="/authentication/loginView")
def settingsUpdateView(request, user_id):
    if request.method == "POST" and "update_user_btn" in request.POST:
        user = get_object_or_404(get_user_model(), pk = user_id)
        user.first_name = request.POST.get("first_name")
        user.last_name = request.POST.get("last_name")
        user.email = request.POST.get("email")
        user.save()
        messages.success(request, f"User was updated successfully!")
        return redirect("phishingDetector:settingsView")

@cache_control(no_cache = True, privacy = True, must_revalidate = True, no_store = True)
@login_required(login_url="/authentication/loginView")
def userAuthorizationView(request, user_id):
    if request.method == "POST" and "authorize_user_btn" in request.POST:
        user = get_object_or_404(get_user_model(), pk = user_id)
        form = AuthorizationForm(request.POST or None, instance = user)
        if not Authorization.objects.filter(id = user_id).exists():
            Authorization.objects.create(
                user = user,
                view_dashboard = request.POST.get("view_dashboard"),
                view_message = request.POST.get("view_message"),
                view_chat = request.POST.get("view_chat"),
                view_setting = request.POST.get("view_setting"),
                view_logs = request.POST.get("view_logs"),
            )
            messages.success(request, f"User was authorized successfully!")
            return redirect("phishingDetector:userAuthorizationView", user_id)

        else:
            Authorization.objects.filter(id = user_id).update(
                user = user,
                view_dashboard = request.POST.get("view_dashboard"),
                view_message = request.POST.get("view_message"),
                view_chat = request.POST.get("view_chat"),
                view_setting = request.POST.get("view_setting"),
                view_logs = request.POST.get("view_logs"),
            )
            messages.success(request, f"User was authorized successfully!")
            return redirect("phishingDetector:userAuthorizationView", user_id)
    
    user = get_object_or_404(get_user_model(), pk = user_id)
    get_user = Authorization.objects.filter(user = user).first()
    form = AuthorizationForm(instance = get_user)    
    templates = "phishingDetector/authorization.html"
    context = {
        "user":user,
        "get_user":get_user,
        "form":form
    }
    return render(request, templates, context) 