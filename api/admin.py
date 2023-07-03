from django.contrib import admin
from .models import User, ProfileTable, TopicTable, ItemTable, CollectionTable


admin.site.register(CollectionTable)
admin.site.register(User)
admin.site.register(ProfileTable)
admin.site.register(TopicTable)
admin.site.register(ItemTable)