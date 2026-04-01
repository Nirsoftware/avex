from django.urls import path
from .views import *

urlpatterns = [
    # Profile
    path('', ProfileListView.as_view()),
    path('me/', MyProfileView.as_view()),
    path('<int:pk>/', UserProfileView.as_view()),
    path('<int:user_id>/follow/', follow_user),
    path('<int:user_id>/unfollow/', unfollow_user),
    path('<int:user_id>/followers/', user_followers),
    path('me/following/', my_following),
    path('me/followers/', my_followers),
    path('me/suggested/', suggested_alumni),
    path('<int:user_id>/mutual/', mutual_following),

    # Experience
    path('experience/', ExperienceCreateView.as_view()),
    path('experience/<int:pk>/', ExperienceUpdateDeleteView.as_view()),

    # Education
    path('education/', EducationCreateView.as_view()),
    path('education/<int:pk>/', EducationUpdateDeleteView.as_view()),

    # Skills
    path('skills/', SkillCreateView.as_view()),
    path('skills/<int:pk>/', SkillDeleteView.as_view()),

    # Recommendations
    path('recommendations/', RecommendationCreateView.as_view()),
    path('recommendations/<int:pk>/', RecommendationUpdateDeleteView.as_view()),

    # Posts
    path('posts/', PostListCreateView.as_view()),
    path('posts/user/<int:user_id>/', UserPostsView.as_view()),
]