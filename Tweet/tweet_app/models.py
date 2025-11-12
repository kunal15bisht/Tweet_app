from django.db import models
from django.contrib.auth.models import User
import os
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

# Create your models here.

class Tweet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(max_length=280)
    photo = models.ImageField(upload_to="photos/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.text[:50]}"

    # ✅ When tweet deleted → delete the image file
    def delete(self, *args, **kwargs):
        if self.photo and os.path.isfile(self.photo.path):
            os.remove(self.photo.path)
        super().delete(*args, **kwargs)

    # ✅ When tweet updated → delete old image if replaced
    def save(self, *args, **kwargs):
        try:
            old = Tweet.objects.get(pk=self.pk)
        except Tweet.DoesNotExist:
            old = None

        if old and old.photo and old.photo != self.photo:
            if os.path.isfile(old.photo.path):
                os.remove(old.photo.path)

        super().save(*args, **kwargs)