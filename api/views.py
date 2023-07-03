from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse,  Http404
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q


from django.shortcuts import get_object_or_404

import json
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import CustomUser, TopicTable, CollectionTable, CollectionTopic, ItemTable, UserItem
from .serializers import CustomUserSerializer, UserItemSerializer, ItemTableSerializer, CollectionTableSerializer, CollectionTopicSerializer, TopicTableSerializer


# in debug we import the sensitive views, otherwise none
# in real production we delete sensitive views file, so even if they 
# # # manage to change DEBUG, it still will return blank
import os 
try: 
    print('getting debug')
    DEBUG = os.getenv('DEBUG')
    print(DEBUG, type(DEBUG))
    if os.getenv('DEBUG') == 'True':
        from .sensitive_views import UserViewSet
        print('imported sensitive views ')
    else:
        raise Exception()
except:
    from dummy_views import DummyView 
    UserViewSet = DummyView 


@csrf_exempt
def user_login(request):
    if request.method == "POST":
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return JsonResponse({
                'status': 'success',
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        else:
            return JsonResponse({"status": "failure"})
    else:
        return JsonResponse({"status": "not post method"})

@csrf_exempt
def user_register(request):
    if request.method == "POST":
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")
        if CustomUser.objects.filter(username=username).exists():
            return JsonResponse({"status": "failure", "error": "Username already exists"})
        elif not username or not password:
            return JsonResponse({"status": "failure", "error": "Empty username or password"})
        else:
            user = CustomUser.objects.create_user(username=username)
            user.set_password(password)  # Hash the password before saving
            user.save()

            refresh = RefreshToken.for_user(user)
            return JsonResponse({
                'status': 'success',
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                }, 
                status=201
            )
    else:
        return JsonResponse({"status": "failure", "error": "Not a POST request"})



@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def home(request):
    user = request.user
    return JsonResponse({
        'username': user.username,
        'password': user.password
    })





# viewing profile
@login_required
def view_profile(request):
    user = request.user
    serializer = CustomUserSerializer(user)
    return JsonResponse(serializer.data, safe=False)

# editing profile
@login_required
def edit_profile(request):
    if request.method == "POST":
        user = request.user
        serializer = CustomUserSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data)
        return JsonResponse(serializer.errors, status=400)
    return JsonResponse({"error": "Invalid method"}, status=400)

# all items for a user
@login_required
def get_all_items(request, username=None):
    if username is None:
        user = request.user
    else:
        user = get_object_or_404(CustomUser, username=username)
    if user == request.user:
        user_items = UserItem.objects.filter(user=user)
    else:
        user_items = UserItem.objects.filter(Q(user=user) & (Q(visibility='global_edit') | Q(visibility='global_view')))
    
    serializer = UserItemSerializer(user_items, many=True)
    return JsonResponse(serializer.data, safe=False)

# all topics for a user
@login_required
def get_all_topics(request, username=None):
    if username is None:
        user = request.user
    else:
        user = get_object_or_404(CustomUser, username=username)
    if user == request.user:
        topics = TopicTable.objects.filter(user=user)
    else:
        topics = TopicTable.objects.filter(Q(user=user) & (Q(visibility='global_edit') | Q(visibility='global_view')))
    serializer = TopicTableSerializer(topics, many=True)
    return JsonResponse(serializer.data, safe=False)

# all collections for a user
@login_required
def get_all_collections(request, username=None):
    if username is None:
        user = request.user
    else:
        user = get_object_or_404(CustomUser, username=username)
    if user == request.user:
        collections = CollectionTable.objects.filter(user=user)
    else:
        collections = CollectionTable.objects.filter(Q(user=user) & (Q(visibility='global_edit') | Q(visibility='global_view')))
    serializer = CollectionTableSerializer(collections, many=True)
    return JsonResponse(serializer.data, safe=False)


# create a collection under a specific user. Only needs to specify a name
@login_required
def create_collection(request):
    if request.method == "POST":
        data = json.loads(request.body)
        data["user"] = request.user.id
        serializer = CollectionTableSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)
    return JsonResponse({"error": "Invalid method"}, status=400)

# create a topic under a specific user. Only needs to specify a name
@login_required
def create_topic(request):
    if request.method == "POST":
        data = json.loads(request.body)
        data["user"] = request.user.id
        serializer = TopicTableSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)
    return JsonResponse({"error": "Invalid method"}, status=400)

# COMPLICATED: edit_topics_in_collection and the next couple of methods involve more complex operations
# It's hard to implement these without knowing the specific interactions between users, collections, and topics
# You will likely need to add more information in the request and then process this on the server side.

# for all of these, we need to first check that you have access. 
# for making changes to collections and topics, you always have access if you are the user owner
# if visibility is 'global_edit', then you also can make changes
# otherwise, you cannot perform the action, and it should return an error


# edit topics in a collection
# ARGS: list of
# collection
# topic
# what='add','del','flip_activity' 
# FUNCTION: if add or del, we just add to the CollectionTopic and initialize is_active = True, if what=='flip_activity' just not the is_active field. 
@login_required
def edit_topics_in_collection(request):
    if request.method == "POST":
        collection_id = request.data.get('collection')
        topic_ids = request.data.get('topics')
        action = request.data.get('what')

        # Fetch the collection
        collection = get_object_or_404(CollectionTable, id=collection_id)

        # Check if the user has access
        if collection.user != request.user and collection.visibility != 'global_edit':
            return JsonResponse({"error": "Unauthorized"}, status=401)

        for topic_id in topic_ids:
            topic = get_object_or_404(TopicTable, id=topic_id)
            if action == 'add':
                CollectionTopic.objects.create(collection=collection, topic=topic, is_active=True)
            elif action == 'del':
                CollectionTopic.objects.filter(collection=collection, topic=topic).delete()
            elif action == 'flip_activity':
                collection_topic = get_object_or_404(CollectionTopic, collection=collection, topic=topic)
                collection_topic.is_active = not collection_topic.is_active
                collection_topic.save()

        return JsonResponse({"status": "success"}, status=200)

    return JsonResponse({"error": "Invalid method"}, status=400)

# Add items to a topic
# ARGS: list of
# topic
# item information: front, back
# FUNCTION: Add items to a topic, this means creating the item in ItemTable, and thus initializing the UserItem
@login_required
def add_items_to_topic(request):
    if request.method == "POST":
        topic_id = request.data.get('topic')
        items = request.data.get('items')

        # Fetch the topic
        topic = get_object_or_404(TopicTable, id=topic_id)

        # Check if the user has access
        if topic.user != request.user and topic.visibility != 'global_edit':
            return JsonResponse({"error": "Unauthorized"}, status=401)

        for item in items:
            item_instance = ItemTable.objects.create(topic=topic, front=item['front'], back=item['back'])
            UserItem.objects.create(item=item_instance, user=request.user)

        return JsonResponse({"status": "success"}, status=200)

    return JsonResponse({"error": "Invalid method"}, status=400)

# Delete items from a topic
# ARGS: list of
# item_id
# FUNCTION: delete all items, this should be as simple as deleting from ItemTable since it will cascade.
@login_required
def delete_items_from_topic(request):
    if request.method == "POST":
        item_ids = request.data.get('items')

        for item_id in item_ids:
            item = get_object_or_404(ItemTable, id=item_id)

            # Check if the user has access
            if item.topic.user != request.user and item.topic.visibility != 'global_edit':
                return JsonResponse({"error": "Unauthorized"}, status=401)

            item.delete()

        return JsonResponse({"status": "success"}, status=200)

    return JsonResponse({"error": "Invalid method"}, status=400)


# fetch the score, front, and back from the least recent n items in the collection
@login_required
def fetch_n_from_collection(request):
    try:
        collection_id = request.GET.get('collection_id')
        n = int(request.GET.get('n'))
        user = request.user

        collection = CollectionTable.objects.get(id=collection_id)
    except:
        raise Http404("Invalid request")

    if not (collection.user == user or collection.visibility in ('global_edit', 'global_view')):
        raise Http404("The user does not have access to this collection")

    topics_in_collection = collection.topics.all()

    user_items = UserItem.objects.filter(
        user=user,
        item__topic__in=topics_in_collection
    ).select_related('item').order_by('last_seen')[:n]

    results = []
    for user_item in user_items:
        results.append({
            'front': user_item.item.front,
            'back': user_item.item.back,
            'score': user_item.score,
        })

    return JsonResponse(results, safe=False)

@login_required
def update_n_items_user(request):
    MAX_SCORE = os.getenv('MAX_SCORE')
    if request.method == "POST":
        data = json.loads(request.body)
        items_data = data.get("items", [])
        for item_data in items_data:
            item_id = item_data.get("id")
            increment = item_data.get("increment")
            user_item = get_object_or_404(UserItem, id=item_id, user=request.user)
            user_item.score = min(max(0, user_item.score + increment), MAX_SCORE)
            user_item.save()
        return JsonResponse({"status": "success"})
    return JsonResponse({"error": "Invalid method"}, status=400)
