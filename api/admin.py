from django.contrib import admin
from .models import CustomUser, TopicTable, CollectionTable, CollectionTopic, ItemTable, UserItem


admin.site.register(CustomUser)
admin.site.register(CollectionTable)
admin.site.register(CollectionTopic)
admin.site.register(TopicTable)
admin.site.register(ItemTable)
admin.site.register(UserItem)