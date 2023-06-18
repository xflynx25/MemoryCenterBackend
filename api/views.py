from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

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

from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

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
        if User.objects.filter(username=username).exists():
            return JsonResponse({"status": "failure", "error": "Username already exists"})
        elif not username or not password:
            return JsonResponse({"status": "failure", "error": "Empty username or password"})
        else:
            user = User.objects.create_user(username=username)
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