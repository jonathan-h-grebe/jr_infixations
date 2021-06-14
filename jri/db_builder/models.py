from django.db import models
from django.utils import timezone
from django.utils.timezone import localtime
# Create your models here.

SOURCE_CHOICES = [
    ("youtube","other")
]


class Infixation(models.Model):
    infixation = models.CharField(max_length=50)
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, default=SOURCE_CHOICES[0])
    vid_id = models.CharField(max_length=11)
    comment_thread_id = models.CharField(max_length=11)
    comment_id = models.CharField(max_length=11)
    vid_title = models.CharField(max_length=50, blank=True)
    date_added = models.DateTimeField(default=timezone.now)
    likes = models.IntegerField(default=0)

    def __str__(self):
        return self.infixation


class Checked_Vids(models.Model):
    vid_id = models.CharField(max_length=11, primary_key=True)
    vid_title = models.CharField(max_length=50, blank=True)
    checked_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.vid_title


class Checked_CommentThreads(models.Model):
    comment_thread_id = models.CharField(max_length=11)
    vid_title = models.CharField(max_length=50, blank=True)
    checked_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.comment_thread_id

class Part_Checked_Vids(models.Model):
    vid_id  = models.CharField(max_length=11, primary_key=True)
    next_page_token = models.CharField(max_length=120)
    vid_title = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.vid_title
