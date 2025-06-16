from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.cache import cache_control
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.conf import settings

from .models import *
from .tasks import process_phishing_data
from authentication.models import *
from authentication.forms import *
from supabase import create_client

import os
import csv
import json
import re
import pandas as pd
import joblib
from PIL import Image
from dotenv import load_dotenv
import pytesseract

# Load environment and Supabase client
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

model = joblib.load('logistic_phishing_model.pkl')  # Trained ML model

# ========== UTILITIES ==========

def extract_text_from_image(image_path):
    try:
        image = Image.open(image_path)
        return pytesseract.image_to_string(image)
    except Exception as e:
        print(f"Error reading image: {e}")
        return ""

def detect_phishing(messages_df):
    results = []
    for _, row in messages_df.iterrows():
        phishing_detected = False
        reasons = []

        message_text = row.get('message_text', '')
        if pd.notnull(message_text) and message_text.strip():
            if model.predict([message_text])[0] == 1:
                phishing_detected = True
                reasons.append("Text-based phishing (model)")

        if row.get("is_image") and pd.notnull(row.get("image_path")):
            extracted_text = extract_text_from_image(row["image_path"])
            if extracted_text.strip():
                if model.predict([extracted_text])[0] == 1:
                    phishing_detected = True
                    reasons.append("Image-based phishing (model)")

        results.append({
            "message_id": row["id"],
            "message_body": message_text,
            "sender_id": str(row.get("sender_id")),
            "receiver_id": str(row.get("recipient_id")),
            "is_phishing": phishing_detected,
            "reasons": ", ".join(reasons)
        })

    return pd.DataFrame(results)

# ========== VIEWS ==========

@login_required(login_url="/authentication/loginView")
@cache_control(no_cache=True, privacy=True, must_revalidate=True, no_store=True)
def homeView(request):
    chats = supabase.table("chats").select("*").execute().data
    chat_members = supabase.table("chats").select("chat_members").execute().data
    accounts = supabase.table("account").select("*").execute().data
    messages = supabase.table("messages").select("*").execute().data
    results = supabase.table("results").select("*").execute().data

    total_chats = len(chats)
    total_messages = len(messages)

    df_messages = pd.DataFrame(messages)
    results_df = detect_phishing(df_messages)
    results_list = results_df.to_dict(orient="records")

    phishing_count = sum(1 for msg in results_list if msg['is_phishing'])
    non_phishing_count = sum(1 for msg in results_list if not msg['is_phishing'])

    payload = []
    for msg in results_list:
        payload.append({
            "message_id": msg.get("message_id"),
            "message_body": msg.get("message_body"),
            "sender_name": msg.get("sender_id"),
            "recipient_id": msg.get("receiver_id"),
            "status" : msg.get("is_phishing"),
        })

    if payload:
        supabase.table("results").upsert(payload).execute()

    return render(request, "phishingDetector/home.html", {
        "chats": chats,
        "results":results,
        "get_total_chats": total_chats,
        "get_total_messages": total_messages,
        "chat_members": chat_members,
        "accounts": accounts,
        "is_phishing_messages_total": phishing_count,
        "not_phishing_messages_total": non_phishing_count,
    })

@login_required(login_url="/authentication/loginView")
@cache_control(no_cache=True, privacy=True, must_revalidate=True, no_store=True)
def chatsView(request):
    chats = supabase.table("chats").select("*").execute().data
    accounts = supabase.table("account").select("*").execute().data
    return render(request, "phishingDetector/chats.html", {
        "chats": chats,
        "accounts": accounts
    })

@login_required(login_url="/authentication/loginView")
@cache_control(no_cache=True, privacy=True, must_revalidate=True, no_store=True)
def messagesView(request):
    messages = supabase.table("messages").select("*").execute().data
    accounts = supabase.table("account").select("*").execute().data
    chats = supabase.table("chats").select("*").execute().data

    df = pd.DataFrame(messages)
    results_df = detect_phishing(df)
    results_list = results_df.to_dict(orient="records")

    sender_lookup = {
        str(acc["uid"]): f"{acc.get('first_name', '')} {acc.get('last_name', '')}".strip()
        for acc in accounts
    }

    receiver_lookup = {
        str(chat["id"]): chat.get("chat_name", "")
        for chat in chats
    }

    csv_path = os.path.join(settings.BASE_DIR, "message_phishing_detection.csv")
    existing_ids = set()

    if os.path.exists(csv_path):
        with open(csv_path, mode="r", encoding="utf-8") as f:
            existing_ids = {row["message_id"] for row in csv.DictReader(f)}

    new_rows = []
    for msg in results_list:
        if msg["message_id"] not in existing_ids:
            is_phishing = int(msg["is_phishing"])
            new_rows.append([
                msg["message_id"],
                msg["message_body"],
                msg["sender_id"],
                msg["receiver_id"],
                is_phishing,
                msg["reasons"]
            ])

            if not PhishingDetection.objects.filter(message_id=msg["message_id"]).exists():
                PhishingDetection.objects.create(
                    message_id=msg["message_id"],
                    message_body=msg["message_body"],
                    sender=msg["sender_id"],
                    receiver=msg["receiver_id"],
                    is_phishing=bool(is_phishing),
                    reasons=msg["reasons"]
                )

    if new_rows:
        write_header = not os.path.exists(csv_path)
        with open(csv_path, mode="a", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(["message_id", "message_text", "sender_id", "recipient_id", "is_phishing", "reasons"])
            writer.writerows(new_rows)

    process_phishing_data()

    return render(request, "phishingDetector/messages.html", {
        "chat_messages": messages,
        "accounts": accounts,
        "chats": chats,
        "results_list": results_list,
        "phishing_detections": PhishingDetection.objects.all().order_by("-id")
    })

# ===== Settings Views =====

@login_required(login_url="/authentication/loginView")
@cache_control(no_cache=True, privacy=True, must_revalidate=True, no_store=True)
def settingsView(request):
    return render(request, "phishingDetector/settings.html", {
        "form": AuthorizationForm(),
        "users": get_user_model().objects.all()
    })

@login_required(login_url="/authentication/loginView")
@cache_control(no_cache=True, privacy=True, must_revalidate=True, no_store=True)
def settingsDeleteView(request, user_id):
    if request.method == "POST" and "delete_user_btn" in request.POST:
        user = get_user_model().objects.filter(pk=user_id).first()
        user.delete()
        messages.success(request, "User deleted successfully!")
    return redirect("phishingDetector:settingsView")

@login_required(login_url="/authentication/loginView")
@cache_control(no_cache=True, privacy=True, must_revalidate=True, no_store=True)
def settingsUpdateView(request, user_id):
    if request.method == "POST" and "update_user_btn" in request.POST:
        user = get_object_or_404(get_user_model(), pk=user_id)
        user.first_name = request.POST.get("first_name")
        user.last_name = request.POST.get("last_name")
        user.email = request.POST.get("email")
        user.save()
        messages.success(request, "User updated successfully!")
    return redirect("phishingDetector:settingsView")

@login_required(login_url="/authentication/loginView")
@cache_control(no_cache=True, privacy=True, must_revalidate=True, no_store=True)
def userAuthorizationView(request, user_id):
    user = get_object_or_404(get_user_model(), pk=user_id)
    auth = Authorization.objects.filter(user=user).first()
    form = AuthorizationForm(request.POST or None, instance=auth)

    if request.method == "POST" and "authorize_user_btn" in request.POST:
        values = {
            "view_dashboard": request.POST.get("view_dashboard"),
            "view_message": request.POST.get("view_message"),
            "view_chat": request.POST.get("view_chat"),
            "view_setting": request.POST.get("view_setting"),
            "view_logs": request.POST.get("view_logs")
        }
        if auth:
            Authorization.objects.filter(user=user).update(**values)
        else:
            Authorization.objects.create(user=user, **values)
        messages.success(request, "User authorization updated!")
        return redirect("phishingDetector:userAuthorizationView", user_id)

    return render(request, "phishingDetector/authorization.html", {
        "user": user,
        "get_user": auth,
        "form": form
    })

# ===== Celery Related =====

def get_latest_phishing_results(request):
    response = supabase.table("results").select("*").order("id", desc=True).limit(10).execute()
    return JsonResponse(response.data, safe=False)

def run_task(request):
    process_phishing_data.delay()
    return HttpResponse("Task started!")
