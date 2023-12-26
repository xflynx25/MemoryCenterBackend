from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse,  Http404
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.utils import timezone

from django.shortcuts import get_object_or_404


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

import json
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import CustomUser, TopicTable, CollectionTable, CollectionTopic, ItemTable, UserItem, TopicItem
from .serializers import CustomUserSerializer, UserItemSerializer, ItemTableSerializer, CollectionTableSerializer,\
      CollectionTopicSerializer, TopicTableSerializer, GetTopicTableSerializer
      
from datetime import datetime, timedelta
from django.utils import timezone


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
    from .dummy_views import DummyView 
    UserViewSet = DummyView 


@csrf_exempt
@api_view(['POST'])
def user_login(request):
    print('inside user login')
    data = request.data
    username = data.get("username")
    print('passed after get username')
    password = data.get("password")
    user = authenticate(request, username=username, password=password)
    print('user is : ', user)
    if user is not None:
        refresh = RefreshToken.for_user(user)
        response =  Response({
            'status': 'success',
            'user_id': user.id,  # Include the user ID in the response
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })
        print(f'Returning from user login: {response}')
        return response
    else:
        return Response({"status": "failure", "error": "Not a valid combo bro"})


@csrf_exempt
@api_view(['POST'])
def user_register(request):
    data = request.data
    print(f"Received data: {data}")  # Log the received data

    username = data.get("username")
    password = data.get("password")
    secret_message = data.get("secret_message")  # Retrieve the secret message from the request
    
    # Log the received credentials
    print(f"Username: {username}, Password: {password}, Secret Message: {secret_message}")

    # Get the list of allowed usernames from the environment variable
    allowed_usernames = os.environ.get('ALLOWED_USERNAMES', '').split(',')
    
    # Retrieve the expected secret message from the environment variable
    expected_secret_message = os.environ.get('SECRET_MESSAGE_SIGNUP', '')
    
    # Log the environment variable values
    print(f"Allowed Usernames: {allowed_usernames}, Expected Secret Message: {expected_secret_message}")

    if CustomUser.objects.filter(username=username).exists():
        print("Error: Username already exists")
        return Response({"status": "failure", "error": "Username already exists"}, status=400)
    elif not username or not password:
        print("Error: Empty username or password")
        return Response({"status": "failure", "error": "Empty username or password"}, status=400)
    elif username not in allowed_usernames:
        print("Error: Username is not allowed")
        return Response({"status": "failure", "error": "Username is not allowed"}, status=400)
    elif secret_message != expected_secret_message:  # Check the secret message
        print("Error: Invalid secret message")
        return Response({"status": "failure", "error": "Invalid secret message"}, status=400)
    else:
        print('about to make custom user')
        user = CustomUser.objects.create_user(username=username)
        print('created user')
        user.set_password(password)
        print('set password')
        user.save()
        print('saved')

        refresh = RefreshToken.for_user(user)
        print("User registered successfully")
        return Response({
            'status': 'success',
            'user_id': user.id,  # Include the user ID in the response
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            },
            status=201
        )

    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_users(request):
    this_user = CustomUser.objects.filter(id=request.user.id)
    other_users = CustomUser.objects.exclude(id=request.user.id)
    
    # Retrieve and serialize this user
    serializer_this = CustomUserSerializer(this_user, many=True)
    this_user_data = serializer_this.data[0] if serializer_this.data else {}
    
    # Retrieve and serialize other users
    serializer_others = CustomUserSerializer(other_users, many=True)
    other_users_data = serializer_others.data
    
    # Combine the data
    all_users_data = [this_user_data] + other_users_data
    
    response_data = {'all_users': all_users_data}
    
    print('Returning from get_all_users', response_data)
    return Response(response_data)





"""
=====
HELPERS
=====
"""
def get_user(request, user_id):
    if user_id is None:
        return request.user
    else:
        return get_object_or_404(CustomUser, id=user_id)


def get_objects(user, request_user, model, serializer, context=None):
    if user == request_user:
        objects = model.objects.filter(user=user)
    else:
        objects = model.objects.filter(Q(user=user) & (Q(visibility='global_edit') | Q(visibility='global_view')))
    
    # Get the data with the request in the context to access it in the serializer
    return serializer(objects, many=True, context=context).data



# does user have access_type ('view' or 'edit') to object (obj)
# later can extend for friends
def has_access(obj, user, access_type):
    if access_type == 'edit':
        if obj.user != user and obj.visibility != 'global_edit':
            return False
    elif access_type == 'view':
        if not (obj.user == user or obj.visibility in ('global_edit', 'global_view')):
            return False 
    return True 


"""
====================
FUNCTIONALITY VIEWS
====================
"""

# viewing profile
#-- request: {userid} or none if viewing self
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_profile(request, user_id=None):
    user = get_user(request, user_id)
    serializer = CustomUserSerializer(user)
    return Response(serializer.data)

# editing profile
#-- request: one or more fields, with the new values
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def edit_profile(request):
    user = request.user
    serializer = CustomUserSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=400)

#-- request: empty
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_items(request, topic_id = None):
    user_items = UserItem.objects.filter(user=request.user)
    serializer = UserItemSerializer(user_items, many=True)
    return Response(serializer.data, content_type='application/json; charset=utf-8')

    # need to implement for the topic_ids, and also clarify the api back to the front end. Probably still return same thing, and just parse it front. 
    # but problem with this is it is returning the scores of everyone using the card...no good. So you want to actually always only get your scores:
    # so maybe i should also implement for a particular user id 
    # RESPONSE: 200 - Lo {'id': I, 'last_seen': DT, 'score': I, 'front': S, 'back':S, 'users': LoI} 

    # it is actually such a mess, because sometimes I might want items for everybody, or sometimes I am asking for your scores. 
    # so maybe this should be closer to fetch_n_from_profile 
    # and then a seperate thing for the display. 
    # because that's what I wanted originally, you just have the display at first, and then you can go into edit mode. 
    # but i can't just pull all items, bcz it could be a lot
    # so we are at a design crossroads. 

#-- request: {userid} or none if viewing self
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_topics(request, user_id=None):
    user = get_user(request, user_id)
    context = {'request_user': request.user, 'profile_user_id': user.id}
    data = get_objects(user, request.user, TopicTable, GetTopicTableSerializer, context=context)
    return Response(data, content_type='application/json; charset=utf-8')


#-- request: {userid} or none if viewing self
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_collections(request, user_id=None):
    user = get_user(request, user_id)
    data = get_objects(user, request.user, CollectionTable, CollectionTableSerializer)
    return Response(data, content_type='application/json; charset=utf-8')


"""-------------------"""
"""CUURENTLY NOT USING SOME"""
"""-------------------"""
#-- request: {userid} or none if viewing self
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_subtopics_collection(request, collection_id):
    user = request.user
    data = get_objects(user, request.user, CollectionTable, CollectionTableSerializer)
    #user_items = UserItem.objects.filter(user=request.user)
    pass


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_topic_items(request, topic_id):
    # Fetch the topic
    topic = get_object_or_404(TopicTable, id=topic_id)

    # Check if the user has access
    if not has_access(topic, request.user, 'view'):
        return Response({"error": "Unauthorized topic items access"}, status=401)

    # Fetch the items related to the topic
    topic_items = TopicItem.objects.filter(topic=topic)

    # Serialize the items
    item_list = [ItemTableSerializer(item.item).data for item in topic_items]

    return Response({"items": item_list}, content_type='application/json; charset=utf-8')


#-- request: {userid} or none if viewing self
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_subusers_item(request, collection_id):
    pass



"""-------------------"""
"""CUURENTLY NOT USING END"""
"""-------------------"""
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_collection(request):
    collection_id = request.data.get('collection_id')

    if not collection_id:
        return Response({"error": "No collection id provided"}, status=400)

    # Fetch the collection
    collection = get_object_or_404(CollectionTable, id=collection_id)

    # Check if the user has access
    if not has_access(collection, request.user, 'edit'):
        return Response({"error": "Unauthorized Collection"}, status=401)
    
    collection.delete()

    return Response({"success": "Collection deleted successfully"}, status=200)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_topic(request):
    topic_id = request.data.get('topic_id')
    if not topic_id:
        return Response({"error": "No topic id provided"}, status=400)

    # Fetch the collection
    topic = get_object_or_404(TopicTable, id=topic_id)

    # Check if the user has access
    if not has_access(topic, request.user, 'edit'):
        return Response({"error": "Unauthorized Topic"}, status=401)

    # First, delete all CollectionTopic instances associated with the topic
    CollectionTopic.objects.filter(topic=topic).delete()

    # Then, delete the topic itself
    topic.delete()

    return Response({"success": "Topic deleted successfully"}, status=200)





#-- request: req {collection_name} optional {description, visibility}
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_collection(request):
    data = request.data.copy()
    collection_name = data.get('collection_name')
    if not collection_name:
        return Response({"error": "No collection name provided"}, status=400)

    data["user"] = request.user.id
    serializer = CollectionTableSerializer(data=data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)

#-- request: req {topic_name} optional {description, visibility}
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_topic(request):
    data = request.data.copy()
    topic_name = data.get('topic_name')
    if not topic_name:
        return Response({"error": "No topic name provided"}, status=400)

    data["user"] = request.user.id
    serializer = TopicTableSerializer(data=data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)

# FUNCTION: if add or del, we just add to the CollectionTopic and initialize is_active = True, if what=='update' just not the is_active field. 
#-- request: required {collection_id, topic_edits -> [[topic_id, what], [topic_id, what], ...]} where what='add','delete','update' 
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def edit_topics_in_collection(request):
    collection_id = request.data.get('collection_id')
    topic_edits = request.data.get('topic_edits')

    # Fetch the collection
    collection = get_object_or_404(CollectionTable, id=collection_id)

    # Check if the user has access
    if not has_access(collection, request.user, 'edit'):
        return Response({"error": "Unauthorized Collection"}, status=401)

    for topic_edit in topic_edits:
        topic_id, action = topic_edit
        topic = get_object_or_404(TopicTable, id=topic_id)
        # Check if the user has access
        if not has_access(topic, request.user, 'edit'):
            return Response({"error": "Unauthorized Topic"}, status=401)
        
        if action == 'add':
            CollectionTopic.objects.create(collection=collection, topic=topic, is_active=True)
        elif action == 'delete':
            #collection.topics.remove(topic)
            CollectionTopic.objects.filter(collection=collection, topic=topic).delete()
        elif action == 'update':
            collection_topic = get_object_or_404(CollectionTopic, collection=collection, topic=topic)
            collection_topic.is_active = not collection_topic.is_active
            collection_topic.save()

    return Response({"status": "success"}, status=200)





# item information: front, back
# FUNCTION: Add items to a topic, this means creating the item in ItemTable, and thus initializing the UserItem
# initialize the user item with the user. it is done 
#-- request: required {topic_id, items -> [[front, back], [front, back], ...]}
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_items_to_topic(request):
    topic_id = request.data.get('topic_id')
    items = request.data.get('items')

    print(f"Request to add items to topic: {topic_id}")

    # Fetch the topic
    topic = get_object_or_404(TopicTable, id=topic_id)

    # Check if the user has access
    if not has_access(topic, request.user, 'edit'):
        print(f"User {request.user} does not have edit access to topic {topic_id}")
        return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    for item in items:
        try:
            front, back = item
        except: 
            return Response({"error": "Both front and back should be provided."}, status=status.HTTP_400_BAD_REQUEST)

        item_instance = ItemTable.objects.create(front=front, back=back)
        UserItem.objects.create(item=item_instance, user=request.user)
        TopicItem.objects.create(item=item_instance, topic=topic)

        print(f"Added item with front {front}, back {back} to topic {topic_id} for user {request.user}")

    user_items = UserItem.objects.filter(user=request.user).values()
    print(f"Current UserItems for user {request.user}: {user_items}")

    return Response({"status": "success"}, status=status.HTTP_200_OK)


#NOT TESTED
# very similar to edit_topics_in_collection, delete, update
# Delete or updating items from a topic, used to just be deletion so need to change
# FUNCTION: delete all items, this should be as simple as deleting from ItemTable since it will cascade.
#-- request: required {topic_id, item_edits -> [{id, what, front, back}], [item_id, what], ...]} where what='delete','update' , and front/back is '' if what=='delete'
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def edit_items_in_topic(request):
    topic_id = request.data.get('topic')
    item_edits = request.data.get('item_edits')

    # Fetch the topic
    topic = get_object_or_404(TopicTable, id=topic_id) #current db implementation stores items independently so ez to look up

    # Check if the user has access
    if not has_access(item.topic, request.user, 'edit'):
        return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
    
    for item_edit in item_edits:
        item_id = item_edit.get('id')
        action = item_edit.get('what')
        item = get_object_or_404(ItemTable, id=item_id)

        if action == 'delete':
            item.delete()
        elif action == 'update':
            new_front = item_edit.get('front')
            new_back = item_edit.get('back')
            front = new_front if new_front else item.front
            back = new_back if new_back else item.back
            item_serializer = ItemTableSerializer(data={'topic': topic_id, 'front': front, 'back': back})
            if item_serializer.is_valid():
                item_instance = item_serializer.save()

    return Response({"status": "success"}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def edit_items_in_topic_full(request):
    request_data = request.data
    topic_id = request_data.get('topic_id')
    final_items = request_data.get('items')

    # Fetch the topic
    topic = get_object_or_404(TopicTable, id=topic_id)

    # Check if the user has access
    if not has_access(topic, request.user, 'edit'):
        return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    # Get the current items for the topic
    current_item_ids = set(TopicItem.objects.filter(topic=topic).values_list('item__id', flat=True))

    # For each item in final_items, check if it's an addition or an update
    new_item_ids = set()
    for item in final_items:
        id = item.get('id')
        front = item.get('front')
        back = item.get('back')

        # Ignore items where both front and back are blank
        if not (front or back):
            continue

        if id == -1:  # New item to be added
            item_instance = ItemTable.objects.create(front=front, back=back)
            UserItem.objects.create(item=item_instance, user=request.user)
            TopicItem.objects.create(item=item_instance, topic=topic)
            new_item_ids.add(item_instance.id)
        else:  # Existing item to be updated
            existing_item = ItemTable.objects.filter(id=id).first()  # Avoid DoesNotExist exception
            if existing_item is not None:
                existing_item.front = front
                existing_item.back = back
                existing_item.save()
                new_item_ids.add(id)

    # For deletions, delete the item from ItemTable (also removes UserItem and TopicItem entries due to cascade)
    for item_id in current_item_ids - new_item_ids:  # IDs present in current items but not in new items
        ItemTable.objects.filter(id=item_id).delete()

    return Response({"status": "success"}, status=status.HTTP_200_OK)


# note that this works even if we don't provide the blanks, bcz they will just stay. So therefore, can be used in shared objects
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def edit_topics_in_collection_full(request):
    request_data = request.data
    collection_id = request_data.get('collection_id')
    final_topics = request_data.get('topics')
    print('the inside data is ', collection_id, final_topics)

    # Fetch the collection
    collection = get_object_or_404(CollectionTable, id=collection_id)

    # Check if the user has access
    if not has_access(collection, request.user, 'edit'):
        return Response({"error": "Unauthorized collection"}, status=status.HTTP_401_UNAUTHORIZED)
    
    # Check if the user has access
    if collection.user != request.user:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    # Iterate over final_topics to update/create CollectionTopic instances
    for topic_data in final_topics:
        topic_id = topic_data.get('topic_id')
        status = topic_data.get('status')

        # Fetch the topic
        topic = get_object_or_404(TopicTable, id=topic_id)
        
        if not has_access(topic, request.user, 'edit'):
            return Response({"error": "Unauthorized topic"}, status=status.HTTP_401_UNAUTHORIZED)
        

        if status != 'not_selected':
            # Get the CollectionTopic object or create a new one if it doesn't exist
            collection_topic, created = CollectionTopic.objects.get_or_create(
                collection=collection,
                topic=topic,
                defaults={'is_active': status == 'active'}
            )
            if not created:
                # Update is_active field
                collection_topic.is_active = status == 'active'
                collection_topic.save()
        else:
            # Delete the CollectionTopic instance if it exists
            CollectionTopic.objects.filter(collection=collection, topic=topic).delete()

    #Delete CollectionTopic instances not in final_topics # ALTERNATIVE IMPLEMENTATION NEEDED AKA PASS IN not_selected IF WE WANT GLOBALS TO WORK
    CollectionTopic.objects.filter(
        collection=collection
    ).exclude(
        topic_id__in=[topic.get('topic_id') for topic in final_topics]
    ).delete()

    return Response({"status": "success"})


# Fetch the score, front, and back from the least recent n items in the collection, 
# that satisfy the property that score < WAIT_SCORE = 5
#-- request: required {collection_id, n}
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch_n_from_collection(request):
    collection_id = request.GET.get('collection_id')
    n = int(request.GET.get('n'))
    user = request.user

    collection = get_object_or_404(CollectionTable, id=collection_id)
    if not has_access(collection, user, 'view'):
        return Response({"error": "Unauthorized"}, status=401)

    # Get only active topics
    collection_topics = collection.collectiontopic_set.filter(is_active=True)
    active_topics_in_collection = [ct.topic for ct in collection_topics]

    MAX_SCORE_BACKEND = 8
    MAX_SCORE_CLIENT = 4
    LEVEL_A_TIME_FREQUENCY = timedelta(days=7)
    LEVEL_B_TIME_FREQUENCY = timedelta(minutes=30)

    # Fetch all eligible user items
    user_items = UserItem.objects.filter(
        user=user,
        item__topics__in=active_topics_in_collection,
    ).select_related('item')

    # Apply score and time-based filtering
    user_items = [
        user_item for user_item in user_items
        if (
            (user_item.score == MAX_SCORE_BACKEND and timezone.now() - user_item.last_seen >= LEVEL_A_TIME_FREQUENCY) or
            (MAX_SCORE_CLIENT <= user_item.score < MAX_SCORE_BACKEND and timezone.now() - user_item.last_seen >= LEVEL_B_TIME_FREQUENCY) or
            MAX_SCORE_CLIENT > user_item.score
        )
    ]

    # Check if there are no user items after filtering
    if not user_items:
        return Response({"error": "No More Items"}, status=405) # random code. 

    # Sort and limit results
    user_items = sorted(user_items, key=lambda ui: ui.last_seen)[:n]

    serializer = UserItemSerializer(user_items, many=True)
    #print(serializer.data)
    return Response(serializer.data, content_type='application/json; charset=utf-8')


# Increments the score, unless score == MAX_SCORE
#-- request: required {items -> {item_id, increment} where increment is 1 or -1 
# the increment could theoretically be a different number, if the deck is small enough it is called multiple times 
# but that is not good as it bypasses the checks. Hmm... so probably, we should only accept +1
# it also conveniently works for the top level. Since we update the time, it stays same by overflow if we do +1, and goes down if -1. 
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_n_items_user(request):
    MAX_SCORE = 8#int(os.getenv('MAX_SCORE'))
    MAX_SCORE_CLIENT = 4 #int(os.getenv('MAX_SCORE_CLIENT'))
    items_data = request.data.get("items", [])
    for item_data in items_data:
        item_id = item_data.get("item_id")
        increment = item_data.get("increment")
        print(item_id, increment)
        increment = max(min(1, increment), -1) # don't allow the double trouble on the backend side
        user_item = get_object_or_404(UserItem, id=item_id, user=request.user)
        # top level:
        if user_item.score == MAX_SCORE and increment < 0: 
            user_item.score = MAX_SCORE_CLIENT
        # if you fail the B level
        elif user_item.score >= MAX_SCORE_CLIENT and increment < 0: 
            user_item.score = MAX_SCORE_CLIENT - 1
        else: 
            user_item.score = min(max(0, user_item.score + increment), MAX_SCORE)
        user_item.last_seen = timezone.now()
        user_item.save()
    return Response({"status": "success"})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def edit_topic_info(request):
    topic_id = request.data.get('topic_id')
    edits = request.data.get('edits')

    # Ensure topic exists and belongs to the authenticated user
    topic = get_object_or_404(TopicTable, id=topic_id, user=request.user)

    # Ensure user has edit access
    if not has_access(topic, request.user, 'edit'):
        return Response({'detail': 'Not enough permissions'}, status=403)
        
    # Edit fields
    if 'visibility' in edits:
        topic.visibility = edits['visibility']
    if 'description' in edits:
        topic.description = edits['description']
    if 'topic_name' in edits:
        topic.topic_name = edits['topic_name']

    topic.save()

    # Serialize and return updated topic
    serializer = TopicTableSerializer(topic)
    return Response(serializer.data, status=200, content_type='application/json; charset=utf-8')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def edit_collection_info(request):
    collection_id = request.data.get('collection_id')
    edits = request.data.get('edits')

    # Ensure collection exists and belongs to the authenticated user
    collection = get_object_or_404(CollectionTable, id=collection_id, user=request.user)

    # Ensure user has edit access
    if not has_access(collection, request.user, 'edit'):
        return Response({'detail': 'Not enough permissions'}, status=403)

    # Edit fields
    if 'visibility' in edits:
        collection.visibility = edits['visibility']
    if 'description' in edits:
        collection.description = edits['description']
    if 'collection_name' in edits:
        collection.collection_name = edits['collection_name']

    collection.save()

    # Serialize and return updated collection
    serializer = (collection)
    return Response(serializer.data, status=200, content_type='application/json; charset=utf-8')
