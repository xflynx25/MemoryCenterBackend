from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    realname = models.CharField(max_length=50, blank=True)
    description = models.CharField(max_length=200, blank=True)
    awards = models.JSONField(blank=True, null=True)


class TopicTable(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    topicname = models.CharField(max_length=30)
    description = models.CharField(max_length=100, blank=True)
    visibility = models.CharField(max_length=30, default='private')
    #visibility_last_change = models.CharField(max_length=30) # to stop constant switching, time consuming operation, maybe not necessary
    #multimode = models.CharField(max_length=10)


class CollectionTable(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    collection_name = models.CharField(max_length=30)
    description = models.CharField(max_length=750, blank=True)
    visibility = models.CharField(max_length=30, default='private')
    #visibility_last_change = models.CharField(max_length=30) # to stop constant switching, time consuming operation, maybe not necessary
    topics = models.ManyToManyField(TopicTable, through='CollectionTopic')

class CollectionTopic(models.Model):
    collection = models.ForeignKey(CollectionTable, on_delete=models.CASCADE)
    topic = models.ForeignKey(TopicTable, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=False)


class ItemTable(models.Model):
    topic = models.ForeignKey(TopicTable, on_delete=models.CASCADE)
    front = models.CharField(max_length=30)
    back = models.CharField(max_length=30)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, through='UserItem')
    #conceptid = models.IntegerField() # id for gropuing items as the same effective concept, for future multimodal expansion
    #conceptname = models.CharField(max_length=20) # the name for the concept .. future

class UserItem(models.Model):
    item = models.ForeignKey(ItemTable, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    last_seen = models.DateTimeField(auto_now_add=True)
    score = models.PositiveSmallIntegerField(default=0)
