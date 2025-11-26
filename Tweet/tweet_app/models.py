from django.db import models
from django.contrib.auth.models import User
# os is no longer needed for this
from django.db.models.signals import post_delete, pre_save, post_save
from django.dispatch import receiver

# Create your models here.

class Tweet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(max_length=280)
    photo = models.ImageField(upload_to="photos/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(User, related_name='tweet_likes', blank = True)

    def __str__(self):
        return f"{self.user.username} - {self.text[:50]}"
    
    def total_likes(self):
        return self.likes.count()

    # We can remove the custom .delete() and .save() methods
    # The signals below will handle everything


# ✅ When tweet deleted → delete the image file from S3
@receiver(post_delete, sender=Tweet)
def delete_photo_on_tweet_delete(sender, instance, **kwargs):
    """
    Deletes photo from S3 when Tweet is deleted.
    'instance' is the Tweet object that was deleted.
    """
    if instance.photo:
        instance.photo.delete(save=False)

# ✅ When tweet updated → delete old image if replaced
@receiver(pre_save, sender=Tweet)
def delete_old_photo_on_update(sender, instance, **kwargs):
    """
    Deletes old photo from S3 when a Tweet is updated with a new photo.
    """
    # if this is a new object, it won't have a pk, so just return
    if not instance.pk:
        return

    try:
        # Get the 'old' version of the object from the database
        old_tweet = Tweet.objects.get(pk=instance.pk)
    except Tweet.DoesNotExist:
        return # Object is new, so no old photo to delete

    # Check if the photo field has changed, and if the old photo exists
    if old_tweet.photo and old_tweet.photo != instance.photo:
        # Delete the old photo from S3
        old_tweet.photo.delete(save=False)
    




#Profile model to extend User model
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', default='default.jpg', blank=True, null=True)

    def __str__(self):
        return f'{self.user.username} Profile'

# --- SIGNALS (Auto-create Profile when User is created) ---
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()