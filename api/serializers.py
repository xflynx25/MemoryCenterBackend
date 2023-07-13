# this page is for pulling data from the databases, which can be called by the views
from django.contrib.auth.hashers import make_password
from rest_framework import serializers
#from django.contrib.auth.models import User

from .models import CustomUser,TopicTable,CollectionTable,CollectionTopic,ItemTable,UserItem,TopicItem


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'realname', 'description', 'awards']#, 'items']

    """
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            hashed_password = make_password(password)
            instance.password = hashed_password
        instance.save()
        return instance
    """
    
    # we see, that updates have default value to their selected value, if only a partial is passed in. 
    def update(self, instance, validated_data):
        instance.realname = validated_data.get('realname', instance.realname)
        instance.description = validated_data.get('description', instance.description)
        instance.awards = validated_data.get('awards', instance.awards)
        instance.save()
        return instance

    def to_representation(self, instance):
        rep = super(CustomUserSerializer, self).to_representation(instance)
        #rep['password'] = "*****" # to hide the password
        return rep


class ItemTableSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemTable
        fields = ['id', 'front', 'back', 'users', 'topics']


class UserItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserItem
        fields = ['id', 'item', 'user', 'last_seen', 'score']

class TopicTableSerializer(serializers.ModelSerializer):
    items = ItemTableSerializer(many=True, read_only=True)

    class Meta:
        model = TopicTable
        fields = ['id', 'user', 'topic_name', 'description', 'visibility', 'items', 'collections'] 


class CollectionTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectionTopic
        fields = ['id', 'collection', 'topic', 'is_active']


class CollectionTableSerializer(serializers.ModelSerializer):
    topics = TopicTableSerializer(many=True, read_only=True) #maybe will chnage this rather to collectiontopic

    class Meta:
        model = CollectionTable
        fields = ['id', 'user', 'collection_name', 'description', 'visibility', 'topics']


        
class TopicItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = TopicItem
        fields = ['id', 'item', 'topic', 'genre']

