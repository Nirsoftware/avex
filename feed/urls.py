from django.urls import path
from .views import (
    PostListCreateView, PostDetailView,
    CommentListCreateView, CommentDetailView,
    like_toggle, RepostCreateView,
    PostAnalyticsView, NotificationListView,
    mark_notification_read, mark_all_notifications_read,
    post_link, track_view, PublicPostDetailView, public_post_page,
    post_likes_list, post_reposters_list,
    trending_news_list
)

urlpatterns = [
    path('posts/', PostListCreateView.as_view(), name='post-list-create'),
    path('posts/<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('posts/<int:pk>/public/', PublicPostDetailView.as_view(), name='post-public'),
    path('posts/<int:post_id>/comments/', CommentListCreateView.as_view(), name='comment-list-create'),
    path('comments/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),
    path('like/<str:content_type>/<int:object_id>/', like_toggle, name='like-toggle'),
    path('posts/<int:post_id>/repost/', RepostCreateView.as_view(), name='repost-create'),
    path('posts/<int:post_id>/analytics/', PostAnalyticsView.as_view(), name='post-analytics'),
    path('posts/<int:post_id>/likes/', post_likes_list, name='post-likes-list'),
    path('posts/<int:post_id>/reposters/', post_reposters_list, name='post-reposters-list'),
    path('posts/<int:post_id>/link/', post_link, name='post-link'),
    path('posts/<int:post_id>/view/', track_view, name='track-view'),
    path('trending/news/', trending_news_list, name='trending-news'),
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:notification_id>/read/', mark_notification_read, name='mark-notification-read'),
    path('notifications/read-all/', mark_all_notifications_read, name='mark-all-notifications-read'),
]
