from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.models import User
from .models import *
from .serializers import *
from .permissions import IsOwner


def signup_view(request):
    if request.method == 'POST':
        if request.content_type and request.content_type.startswith('application/json'):
            import json
            data = json.loads(request.body.decode('utf-8'))
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            if not (username and email and password):
                return JsonResponse({'error': 'Missing fields'}, status=400)
            existing_user = User.objects.filter(username=username).first()
            if existing_user:
                # If the user was created by /api/signup first, allow this endpoint to log in instead of failing
                user = authenticate(request, username=username, password=password)
                if user is None:
                    return JsonResponse({'error': 'Username already exists with different password'}, status=400)
                login(request, user)
                Profile.objects.get_or_create(user=user)
                from rest_framework.authtoken.models import Token
                token, _ = Token.objects.get_or_create(user=user)
                return JsonResponse({'token': token.key, 'user': {'id': user.id, 'username': user.username}})

            user = User.objects.create_user(username=username, email=email, password=password)
            Profile.objects.create(user=user)
            login(request, user)
            from rest_framework.authtoken.models import Token
            token, _ = Token.objects.get_or_create(user=user)
            return JsonResponse({'token': token.key, 'user': {'id': user.id, 'username': user.username}})
        else:
            form = UserCreationForm(request.POST)
            if form.is_valid():
                user = form.save()
                Profile.objects.create(user=user)
                login(request, user)
                return redirect('profile')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})


from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        if request.content_type and request.content_type.startswith('application/json'):
            import json
            try:
                data = json.loads(request.body.decode('utf-8'))
            except (ValueError, TypeError):
                return JsonResponse({'error': 'Invalid JSON body'}, status=400)
            username = data.get('username')
            password = data.get('password')
        else:
            username = request.POST.get('username')
            password = request.POST.get('password')

        if not username or not password:
            if request.content_type and request.content_type.startswith('application/json'):
                return JsonResponse({'error': 'Username and password are required'}, status=400)
            messages.error(request, 'Username and password are required')
            return render(request, 'accounts/login.html')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            from rest_framework.authtoken.models import Token
            token, _ = Token.objects.get_or_create(user=user)
            if request.content_type and request.content_type.startswith('application/json'):
                return JsonResponse({'token': token.key, 'user': {'id': user.id, 'username': user.username}})
            return redirect('profile')

        if request.content_type and request.content_type.startswith('application/json'):
            return JsonResponse({'error': 'Invalid credentials'}, status=400)

        messages.error(request, 'Invalid credentials')
    return render(request, 'accounts/login.html')


def profile_view(request):
    return render(request, 'profile.html')


def feeds_view(request):
    return render(request, 'feeds.html')


class SignupView(generics.CreateAPIView):
    serializer_class = SignupSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')

        if not (username and email and password):
            return Response(
                {'error': 'Missing username, email, or password.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing_user = User.objects.filter(username=username).first()
        if existing_user:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                Profile.objects.get_or_create(user=user)
                from rest_framework.authtoken.models import Token
                token, _ = Token.objects.get_or_create(user=user)
                return Response(
                    {'token': token.key, 'user': UserSerializer(user).data},
                    status=status.HTTP_200_OK,
                )

            return Response(
                {'error': 'Username already exists with a different password, or invalid credentials.'},
                status=status.HTTP_409_CONFLICT,
            )

        # New user signup path
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        Profile.objects.get_or_create(user=user)
        from rest_framework.authtoken.models import Token
        token, _ = Token.objects.get_or_create(user=user)
        response_data = {
            'token': token.key,
            'user': UserSerializer(user).data,
        }
        return Response(response_data, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            from rest_framework.authtoken.models import Token
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key, 'user': {'id': user.id, 'username': user.username}})
        return Response({'error': 'Invalid credentials'}, status=400)


# PROFILE

from rest_framework.parsers import JSONParser, MultiPartParser, FormParser


class MyProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self):
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile


class UserProfileView(generics.RetrieveAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.AllowAny]


class ProfileListView(generics.ListAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.AllowAny]


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def follow_user(request, user_id):
    if request.user.id == user_id:
        return Response({'error': "You can't follow yourself."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        target = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    follow, created = Follow.objects.get_or_create(follower=request.user, following=target)
    if created:
        return Response({'status': 'followed', 'user_id': target.id})
    return Response({'status': 'already following', 'user_id': target.id})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def unfollow_user(request, user_id):
    if request.user.id == user_id:
        return Response({'error': "You can't unfollow yourself."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        target = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    deleted, _ = Follow.objects.filter(follower=request.user, following=target).delete()
    if deleted:
        return Response({'status': 'unfollowed', 'user_id': target.id})
    return Response({'status': 'not following', 'user_id': target.id})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_following(request):
    follows = Follow.objects.filter(follower=request.user).select_related('following')
    users = [follow.following for follow in follows]
    return Response(UserSerializer(users, many=True).data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_followers(request):
    follows = Follow.objects.filter(following=request.user).select_related('follower')
    users = [follow.follower for follow in follows]
    return Response(UserSerializer(users, many=True).data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_followers(request, user_id):
    try:
        target = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    follows = Follow.objects.filter(following=target).select_related('follower')
    users = [follow.follower for follow in follows]
    return Response(UserSerializer(users, many=True, context={'request': request}).data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def suggested_alumni(request):
    following_ids = list(Follow.objects.filter(follower=request.user).values_list('following_id', flat=True))
    excluded_ids = following_ids + [request.user.id]
    recommendations = User.objects.exclude(id__in=excluded_ids)[:15]
    return Response(UserSerializer(recommendations, many=True).data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def mutual_following(request, user_id):
    try:
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    my_following = set(Follow.objects.filter(follower=request.user).values_list('following_id', flat=True))
    their_following = set(Follow.objects.filter(follower=target_user).values_list('following_id', flat=True))
    mutual_ids = my_following.intersection(their_following)

    mutual_users = User.objects.filter(id__in=mutual_ids)
    return Response(UserSerializer(mutual_users, many=True).data)


# EXPERIENCE

class ExperienceCreateView(generics.CreateAPIView):
    serializer_class = ExperienceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        serializer.save(profile=profile)


class ExperienceUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Experience.objects.all()
    serializer_class = ExperienceSerializer
    permission_classes = [permissions.IsAuthenticated]


# EDUCATION

class EducationCreateView(generics.CreateAPIView):
    serializer_class = EducationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        serializer.save(profile=profile)


class EducationUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Education.objects.all()
    serializer_class = EducationSerializer
    permission_classes = [permissions.IsAuthenticated]


# SKILLS

class SkillCreateView(generics.CreateAPIView):
    serializer_class = SkillSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        serializer.save(profile=profile)


class SkillDeleteView(generics.DestroyAPIView):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [permissions.IsAuthenticated]


# RECOMMENDATIONS

class RecommendationCreateView(generics.CreateAPIView):
    serializer_class = RecommendationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        serializer.save(profile=profile)


class RecommendationUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Recommendation.objects.all()
    serializer_class = RecommendationSerializer
    permission_classes = [permissions.IsAuthenticated]


# POSTS

class PostListCreateView(generics.ListCreateAPIView):
    queryset = Post.objects.all().order_by('-created_at')
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class UserPostsView(generics.ListAPIView):
    serializer_class = PostSerializer

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return Post.objects.filter(author__id=user_id).order_by('-created_at')