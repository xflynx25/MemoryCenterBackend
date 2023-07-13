from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    realname = models.CharField(max_length=50, blank=True)
    description = models.CharField(max_length=200, blank=True)
    awards = models.JSONField(blank=True, default=list)

# backward map to TopicTable.topics
class ItemTable(models.Model):
    front = models.CharField(max_length=30)
    back = models.CharField(max_length=30)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, through='UserItem', related_name='items')
    # these concepts should probably be a subtable. 
    #conceptid = models.IntegerField() # id for gropuing items as the same effective concept, for future multimodal expansion
    #conceptname = models.CharField(max_length=20) # the name for the concept .. future

# backward map to ItemTable.items
class UserItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) 
    item = models.ForeignKey(ItemTable, on_delete=models.CASCADE)
    last_seen = models.DateTimeField(auto_now_add=True)
    score = models.PositiveSmallIntegerField(default=0)

# backward map to CollectionTable.collections
class TopicTable(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    topic_name = models.CharField(max_length=30)
    description = models.CharField(max_length=100, blank=True)
    visibility = models.CharField(max_length=30, default='private')
    #visibility_last_change = models.CharField(max_length=30) # to stop constant switching, time consuming operation, maybe not necessary
    #multimode = models.CharField(max_length=10)
    items = models.ManyToManyField(ItemTable, through='TopicItem', blank=True, related_name='topics')

class TopicItem(models.Model):
    topic = models.ForeignKey(TopicTable, on_delete=models.CASCADE)
    item = models.ForeignKey(ItemTable, on_delete=models.CASCADE)
    genre = models.PositiveSmallIntegerField(default=0)

class CollectionTable(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    collection_name = models.CharField(max_length=30)
    description = models.CharField(max_length=750, blank=True)
    visibility = models.CharField(max_length=30, default='private')
    #visibility_last_change = models.CharField(max_length=30) # to stop constant switching, time consuming operation, maybe not necessary
    topics = models.ManyToManyField(TopicTable, through='CollectionTopic', blank=True, related_name='collections')

class CollectionTopic(models.Model):
    collection = models.ForeignKey(CollectionTable, on_delete=models.CASCADE)
    topic = models.ForeignKey(TopicTable, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=False)

