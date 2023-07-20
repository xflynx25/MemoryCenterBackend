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


#class UserItemSerializer(serializers.ModelSerializer):
#   items = ItemTableSerializer(many=True, read_only=True)
#    class Meta:
#        model = UserItem
#        fields = ['id', 'item', 'user', 'last_seen', 'score']

class UserItemSerializer(serializers.ModelSerializer):
    front = serializers.SerializerMethodField()
    back = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()
    
    
    class Meta:
        model = UserItem
        fields = ['id', 'user', 'last_seen', 'score', 'front', 'back']

    def get_front(self, obj):
        return obj.item.front

    def get_back(self, obj):
        return obj.item.back

    # takes care of the weird level property we have. 
    def get_score(self, obj):
        MAX_SCORE_BACKEND = 8 #int(os.getenv('MAX_SCORE_BACKEND'))
        MAX_SCORE_CLIENT = 4 #int(os.getenv('MAX_SCORE_CLIENT'))
        score = obj.score
        return (MAX_SCORE_CLIENT + 1 if score == MAX_SCORE_BACKEND else min(score, MAX_SCORE_CLIENT))



class TopicTableSerializer(serializers.ModelSerializer):
    items = ItemTableSerializer(many=True, read_only=True)

    class Meta:
        model = TopicTable
        fields = ['id', 'user', 'topic_name', 'description', 'visibility', 'items', 'collections'] 


class CollectionTopicSerializer(serializers.ModelSerializer):
    topic_name = serializers.SerializerMethodField()

    class Meta:
        model = CollectionTopic
        fields = ['id', 'collection', 'topic', 'is_active', 'topic_name']

    def get_topic_name(self, obj):
        return obj.topic.topic_name



class CollectionTableSerializer(serializers.ModelSerializer):
    topics = CollectionTopicSerializer(source='collectiontopic_set', many=True, read_only=True)

    class Meta:
        model = CollectionTable
        fields = ['id', 'user', 'collection_name', 'description', 'visibility', 'topics']


        
class TopicItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = TopicItem
        fields = ['id', 'item', 'topic', 'genre']



class GetTopicTableItemSerializer(serializers.ModelSerializer):
    score = serializers.SerializerMethodField()

    class Meta:
        model = ItemTable
        fields = ['id', 'front', 'back', 'score']

    def get_score(self, obj):
        user_item = UserItem.objects.filter(user=self.context['request'], item=obj).first()
        MAX_SCORE_BACKEND = 8 #int(os.getenv('MAX_SCORE_BACKEND'))
        MAX_SCORE_CLIENT = 4 #int(os.getenv('MAX_SCORE_CLIENT'))
        score = user_item.score
        return (MAX_SCORE_CLIENT + 1 if score == MAX_SCORE_BACKEND else min(score, MAX_SCORE_CLIENT))



class GetTopicTableSerializer(serializers.ModelSerializer):
    items = GetTopicTableItemSerializer(many=True, read_only=True)

    class Meta:
        model = TopicTable
        fields = ['id', 'user', 'topic_name', 'description', 'visibility', 'items', 'collections']
