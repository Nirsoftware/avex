from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Post, Comment, Like, Repost, PostAnalytics, Notification, PostView
from django.contrib.contenttypes.models import ContentType


class UserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'avatar_url', 'title', 'followers_count']

    def get_followers_count(self, obj):
        try:
            return obj.followers_relations.count()
        except Exception:
            return 0

    def get_avatar_url(self, obj):
        try:
            if obj.profile.avatar:
                request = self.context.get('request')
                return request.build_absolute_uri(obj.profile.avatar.url) if request else obj.profile.avatar.url
        except Exception:
            pass
        return None

    def get_title(self, obj):
        try:
            return obj.profile.title or ''
        except Exception:
            return ''


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'author', 'post', 'parent_comment', 'content', 'created_at', 'replies', 'likes_count', 'is_liked']
        read_only_fields = ['author', 'post']
        extra_kwargs = {
            'parent_comment': {'required': False, 'allow_null': True},
        }

    def get_replies(self, obj):
        if obj.replies.exists():
            return CommentSerializer(obj.replies.all(), many=True, context=self.context).data
        return []

    def get_likes_count(self, obj):
        ct = ContentType.objects.get_for_model(Comment)
        return Like.objects.filter(content_type=ct, object_id=obj.id).count()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            ct = ContentType.objects.get_for_model(Comment)
            return Like.objects.filter(user=request.user, content_type=ct, object_id=obj.id).exists()
        return False


class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    reposts_count = serializers.SerializerMethodField()
    views_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_reposted = serializers.SerializerMethodField()
    is_commented = serializers.SerializerMethodField()
    original_post_data = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'author', 'content', 'image', 'video', 'link', 'scheduled_at', 'is_published', 'created_at', 'updated_at', 'original_post', 'likes_count', 'comments_count', 'reposts_count', 'views_count', 'is_liked', 'is_reposted', 'is_commented', 'reposted_by', 'original_post_data', 'comments']

    def get_comments(self, obj):
        # Only top-level comments — replies are nested inside each comment via get_replies
        top_level = obj.comments.filter(parent_comment__isnull=True)
        return CommentSerializer(top_level, many=True, context=self.context).data

    def get_likes_count(self, obj):
        ct = ContentType.objects.get_for_model(Post)
        return Like.objects.filter(content_type=ct, object_id=obj.id).count()

    def get_comments_count(self, obj):
        # Only count top-level comments, not replies
        return obj.comments.filter(parent_comment__isnull=True).count()

    def get_reposts_count(self, obj):
        return obj.reshares.count()

    def get_views_count(self, obj):
        return obj.views.count()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            ct = ContentType.objects.get_for_model(Post)
            return Like.objects.filter(user=request.user, content_type=ct, object_id=obj.id).exists()
        return False

    def get_is_reposted(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.reshares.filter(user=request.user).exists()
        return False

    def get_is_commented(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.comments.filter(author=request.user).exists()
        return False

    reposted_by = serializers.SerializerMethodField()

    def get_reposted_by(self, obj):
        if obj.original_post:
            return obj.author.username
        return None

    def get_original_post_data(self, obj):
        if obj.original_post:
            op = obj.original_post
            ct = ContentType.objects.get_for_model(Post)
            likes = Like.objects.filter(content_type=ct, object_id=op.id).count()
            request = self.context.get('request')
            image_url = None
            if op.image:
                image_url = request.build_absolute_uri(op.image.url) if request else op.image.url
            video_url = None
            if op.video:
                video_url = request.build_absolute_uri(op.video.url) if request else op.video.url
            return {
                'id': op.id,
                'author': op.author.username,
                'author_avatar': UserSerializer(op.author, context=self.context).data.get('avatar_url'),
                'author_title': UserSerializer(op.author, context=self.context).data.get('title'),
                'content': op.content,
                'image': image_url,
                'video': video_url,
                'link': op.link,
                'created_at': op.created_at,
                'likes_count': likes,
                'comments_count': op.comments.count(),
                'reposts_count': op.reshares.count(),
            }
        return None


class RepostSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    original_post = PostSerializer(read_only=True)

    class Meta:
        model = Repost
        fields = '__all__'
        read_only_fields = ['user']


class PostAnalyticsSerializer(serializers.ModelSerializer):
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    reposts_count = serializers.SerializerMethodField()

    class Meta:
        model = PostAnalytics
        fields = '__all__'

    def get_likes_count(self, obj):
        ct = ContentType.objects.get_for_model(Post)
        return Like.objects.filter(content_type=ct, object_id=obj.post.id).count()

    def get_comments_count(self, obj):
        return obj.post.comments.count()

    def get_reposts_count(self, obj):
        return obj.post.reshares.count()


class NotificationSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    text = serializers.SerializerMethodField()
    target_url = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'sender', 'notification_type', 'post', 'comment', 'text', 'target_url', 'is_read', 'created_at']

    def get_text(self, obj):
        return obj.get_text()

    def get_target_url(self, obj):
        if obj.target_url:
            return obj.target_url
        if obj.post:
            url = f"/post/{obj.post.id}/"
            if obj.notification_type in ('comment', 'reply') and obj.comment:
                return f"{url}#comment-{obj.comment.id}"
            if obj.notification_type == 'like' and obj.comment:
                return f"{url}#comment-{obj.comment.id}"
            return url
        return '/feeds/'
