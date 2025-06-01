from django.db import models
import uuid

# Create your models here.
class PhishingDetection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message_id = models.CharField(max_length=10,unique=True, blank=True, null=True)   
    message_body = models.TextField(blank=True, null=True)
    sender = models.CharField(max_length=100, blank=True, null=True)
    receiver = models.CharField(max_length=100, blank=True, null=True)
    is_phishing = models.BooleanField(default=False)
    reasons = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        verbose_name = "Phishing detection"
        verbose_name_plural = "Phishing detections"

    def __str__(self):
        return f"Message body: {self.message_body}, Sender: {self.sender}, Receiver: {self.receiver}, Status: {self.is_phishing}"