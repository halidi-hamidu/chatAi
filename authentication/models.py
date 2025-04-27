from django.db import models
from django.contrib.auth.models import User
import uuid

# Create your models here.
class Authorization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False,)
    user = models.ForeignKey(User, related_name="user_authorization", on_delete=models.CASCADE)
    CHOICES = [
        ("Yes", "Yes"),
        ("No", "No"),
    ]
    view_dashboard = models.CharField(max_length=50, choices=CHOICES, default="No")
    view_message = models.CharField(max_length=50, choices=CHOICES, default="No")
    view_chat = models.CharField(max_length=50, choices=CHOICES, default="No")
    view_setting = models.CharField(max_length=50, choices=CHOICES, default="No")
    view_logs = models.CharField(max_length=50, choices=CHOICES, default="No")

    class Meta:
        verbose_name = "Authorization"
        verbose_name_plural = "Authorizations"
    
    def __str__(self):
        return f"Firstname: {self.user.first_name}, Lastname: {self.user.last_name}"