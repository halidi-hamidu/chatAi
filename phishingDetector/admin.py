from django.contrib import admin
from .models import *

# Register your models here.
@admin.register(PhishingDetection)
class PhishingDetectionModel(admin.ModelAdmin):
    list_display = ("id","message_id","message_body","sender","receiver","is_phishing","reasons")
    display_filter = ("id","message_id","message_body","sender","receiver","is_phishing","reasons")