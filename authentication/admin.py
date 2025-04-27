from django.contrib import admin
from .models import *

# Register your models here.
@admin.register(Authorization)
class AuthorizationModel(admin.ModelAdmin):
    list_display = ("id","view_dashboard","view_message","view_chat","view_setting")
    display_filter = ("id","view_dashboard","view_message","view_chat","view_setting")