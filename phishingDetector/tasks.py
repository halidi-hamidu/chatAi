import pandas as pd
from django.conf import settings
from celery import shared_task
from supabase import create_client
from .models import *

# Supabase config
SUPABASE_URL = "https://opflubhudldbaxzamwyr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9wZmx1Ymh1ZGxkYmF4emFtd3lyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQyMTg3OTgsImV4cCI6MjA1OTc5NDc5OH0.uHXoNK1vdeUWfYoW-ZlFEk73tWNsSPYcvJtt4FIkZGQ"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# @shared_task
# def process_phishing_data():
#     try:
#         # Step 1: Query phishing messages from SQLite
#         phishing_records = PhishingDetection.objects.filter(is_phishing=True)

#         # Step 2: Fetch existing message_ids from Supabase
#         existing_ids_resp = supabase.table("results").select("message_id").execute()
#         existing_ids = {item["message_id"] for item in existing_ids_resp.data}

#         # Step 3: Fetch accounts from Supabase
#         accounts_resp = supabase.table("account").select("*").execute()
#         accounts = accounts_resp.data

#         # Step 4: Build uid → full name map
#         account_map = {
#             acc["uid"]: f"{acc.get('first_name', '').title()} {acc.get('last_name', '').title()}"
#             for acc in accounts
#         }

#         # Step 5: Insert only new phishing messages
#         new_inserts = 0
#         for record in phishing_records:
#             if record.message_id in existing_ids:
#                 continue  # skip duplicates

#             sender_name = account_map.get(record.sender, "Unknown")

#             data = {
#                 "sender_id": record.sender,
#                 "recipient_id": record.receiver,
#                 "message_body": record.message_body,
#                 "message_id": record.message_id,
#                 "sender_name": sender_name,
#             }

#             supabase.table("results").insert(data).execute()
#             new_inserts += 1

#         print(f"✅ {new_inserts} new phishing messages inserted into Supabase.")

#     except Exception as e:
#         print(f"❌ Task failed: {e}")

@shared_task
def process_phishing_data():
    try:
        # Step 1: Query phishing messages from SQLite
        phishing_records = PhishingDetection.objects.filter(is_phishing=True)

        if not phishing_records:
            print("ℹ️ No phishing records found.")
            return

        # Step 2: Fetch existing message_ids from Supabase
        existing_ids_resp = supabase.table("results").select("message_id").execute()
        existing_ids = {item["message_id"] for item in existing_ids_resp.data}

        # Step 3: Fetch accounts from Supabase
        accounts_resp = supabase.table("account").select("*").execute()
        accounts = accounts_resp.data

        # Step 4: Build uid → full name map
        account_map = {
            acc["uid"]: f"{acc.get('first_name', '').title()} {acc.get('last_name', '').title()}"
            for acc in accounts
        }

        # Step 5: Collect new records for batch insert
        new_records = []
        for record in phishing_records:
            if record.message_id in existing_ids:
                continue  # Already inserted

            sender_name = account_map.get(record.sender, "Unknown")

            new_records.append({
                "sender_id": record.sender,
                "recipient_id": record.receiver,
                "message_body": record.message_body,
                "message_id": record.message_id,
                "sender_name": sender_name,
            })

        # Step 6: Insert only new records
        if new_records:
            for row in new_records:
                supabase.table("results").insert(row).execute()
            print(f"✅ {len(new_records)} new phishing messages inserted into Supabase.")
        else:
            print("ℹ️ No new phishing messages to insert.")

    except Exception as e:
        print(f"❌ Task failed: {e}")
