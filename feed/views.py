from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render
from django.contrib.auth.models import User
from profiles.models import Follow
from .models import Post, Comment, Like, Repost, PostAnalytics, Notification, PostView
from .serializers import (
    PostSerializer, CommentSerializer, RepostSerializer,
    PostAnalyticsSerializer, NotificationSerializer
)
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def send_notification_ws(notification):
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    payload = NotificationSerializer(notification).data
    group_name = f"user_{notification.recipient.id}"

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'send_notification',
            'notification': payload,
        }
    )


class PostListCreateView(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Post.objects.filter(is_published=True).order_by('-created_at')

    def perform_create(self, serializer):
        scheduled_at = self.request.data.get('scheduled_at')
        is_published = True
        if scheduled_at:
            try:
                sched = timezone.datetime.fromisoformat(scheduled_at)
                if timezone.is_naive(sched):
                    sched = timezone.make_aware(sched)
                is_published = timezone.now() >= sched
            except ValueError:
                pass

        post = serializer.save(author=self.request.user, is_published=is_published, scheduled_at=scheduled_at or None)

        # Notify followers that this user posted
        follower_ids = Follow.objects.filter(following=self.request.user).values_list('follower_id', flat=True)
        for follower_id in follower_ids:
            if follower_id == self.request.user.id:
                continue
            n = Notification.objects.create(
                recipient_id=follower_id,
                sender=self.request.user,
                notification_type='post',
                post=post,
                target_url=f"/post/{post.id}/"
            )
            send_notification_ws(n)


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user)

    def perform_destroy(self, instance):
        # Post can be original or a repost container
        if instance.original_post:
            # Deleting a repost removes the repost entry and associated Repost model record
            Repost.objects.filter(user=instance.author, original_post=instance.original_post).delete()
            instance.delete()
        else:
            # Deleting an original post should remove all reposts of it
            Repost.objects.filter(original_post=instance).delete()
            Post.objects.filter(original_post=instance).delete()
            instance.delete()


class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Comment.objects.filter(post_id=self.kwargs['post_id'], parent_comment__isnull=True)

    def perform_create(self, serializer):
        post = Post.objects.get(id=self.kwargs['post_id'])
        parent_id = self.request.data.get('parent_comment')

        # Resolve to root parent so reply-to-reply threads under the top-level comment
        if parent_id:
            try:
                parent = Comment.objects.get(id=parent_id)
                # If this parent is itself a reply, use its root parent instead
                if parent.parent_comment_id:
                    parent_id = parent.parent_comment_id
            except Comment.DoesNotExist:
                parent_id = None

        comment = serializer.save(author=self.request.user, post=post, parent_comment_id=parent_id)

        # Notify post author on new top-level comment
        if not parent_id and post.author != self.request.user:
            n = Notification.objects.create(
                recipient=post.author,
                sender=self.request.user,
                notification_type='comment',
                post=post,
                comment=comment,
                target_url=f"/post/{post.id}/#comment-{comment.id}"
            )
            send_notification_ws(n)
        # Notify the comment author when someone replies
        elif parent_id:
            try:
                parent_comment = Comment.objects.get(id=parent_id)
                if parent_comment.author != self.request.user:
                    n = Notification.objects.create(
                        recipient=parent_comment.author,
                        sender=self.request.user,
                        notification_type='reply',
                        post=post,
                        comment=comment,
                        target_url=f"/post/{post.id}/#comment-{comment.id}"
                    )
                    send_notification_ws(n)
            except Comment.DoesNotExist:
                pass


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Comment.objects.filter(author=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def like_toggle(request, content_type, object_id):
    if content_type == 'post':
        obj = Post.objects.get(id=object_id)
    elif content_type == 'comment':
        obj = Comment.objects.get(id=object_id)
    else:
        return Response({'error': 'Invalid content type'}, status=400)

    ct = ContentType.objects.get_for_model(obj)
    like, created = Like.objects.get_or_create(user=request.user, content_type=ct, object_id=object_id)

    if not created:
        like.delete()
        return Response({'action': 'unliked'})

    if hasattr(obj, 'author') and obj.author != request.user:
        target = None
        if content_type == 'post':
            target = f"/post/{obj.id}/"
        elif content_type == 'comment' and hasattr(obj, 'post'):
            target = f"/post/{obj.post.id}/#comment-{obj.id}"

        n = Notification.objects.create(
            recipient=obj.author,
            sender=request.user,
            notification_type='like',
            post=obj if content_type == 'post' else getattr(obj, 'post', None),
            comment=obj if content_type == 'comment' else None,
            target_url=target
        )
        send_notification_ws(n)
    return Response({'action': 'liked'})


class RepostCreateView(generics.CreateAPIView):
    serializer_class = RepostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        original_post = Post.objects.get(id=self.kwargs['post_id'])
        repost = serializer.save(user=self.request.user, original_post=original_post)

        # Create a Post entry so reposts appear in the feed inline
        Post.objects.create(
            author=self.request.user,
            content=repost.content or '',
            original_post=original_post,
            is_published=True
        )

        if original_post.author != self.request.user:
            n = Notification.objects.create(
                recipient=original_post.author,
                sender=self.request.user,
                notification_type='repost',
                post=original_post,
                target_url=f"/post/{original_post.id}/"
            )
            send_notification_ws(n)


class PostAnalyticsView(generics.RetrieveAPIView):
    serializer_class = PostAnalyticsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        post = Post.objects.get(id=self.kwargs['post_id'])
        analytics, _ = PostAnalytics.objects.get_or_create(post=post)
        return analytics


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_notification_read(request, notification_id):
    try:
        n = Notification.objects.get(id=notification_id, recipient=request.user)
        n.is_read = True
        n.save()
    except Notification.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)
    return Response({'status': 'read'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_all_notifications_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return Response({'status': 'all read'})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def post_likes_list(request, post_id):
    """Return list of users who liked a post."""
    from django.contrib.auth.models import User
    post = Post.objects.get(id=post_id)
    ct = ContentType.objects.get_for_model(Post)
    likes = Like.objects.filter(content_type=ct, object_id=post_id).select_related('user__profile')
    from .serializers import UserSerializer
    users = [like.user for like in likes]
    data = UserSerializer(users, many=True, context={'request': request}).data
    return Response(data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def post_reposters_list(request, post_id):
    """Return list of users who reposted a post.

    Optional query parameter:
      ?follower_of=<user_id>  -> return only reposts by followers of that user.
    """
    reposts = Repost.objects.filter(original_post_id=post_id).select_related('user__profile')

    follower_of = request.query_params.get('follower_of')
    if follower_of:
        try:
            target = User.objects.get(id=follower_of)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        follower_ids = Follow.objects.filter(following=target).values_list('follower_id', flat=True)
        reposts = reposts.filter(user_id__in=follower_ids)

    from .serializers import UserSerializer
    users = [r.user for r in reposts]
    data = UserSerializer(users, many=True, context={'request': request}).data
    return Response(data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def trending_news_list(request):
    from django.contrib.contenttypes.models import ContentType

    ct = ContentType.objects.get_for_model(Post)

    posts = Post.objects.filter(is_published=True).prefetch_related('comments', 'reshares')
    scored_posts = []

    for post in posts:
        likes = Like.objects.filter(content_type=ct, object_id=post.id).count()
        comments = post.comments.filter(parent_comment__isnull=True).count()
        reposts = post.reshares.count()
        score = likes * 2 + comments * 3 + reposts * 4

        if score > 0:
            scored_posts.append((score, post))

    scored_posts.sort(key=lambda item: item[0], reverse=True)
    top_posts = [post for _, post in scored_posts[:20]]

    serializer = PostSerializer(top_posts, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def post_link(request, post_id):
    Post.objects.get(id=post_id)  # 404 if not found
    link = request.build_absolute_uri(f'/feed/posts/{post_id}/')
    return Response({'link': link})


# Public post view — no authentication required
def public_post_page(request, post_id):
    """Serve post.html with Open Graph meta tags for social media previews."""
    from django.shortcuts import get_object_or_404
    import html as html_module

    post = get_object_or_404(Post, id=post_id, is_published=True)

    # Build OG values
    author = post.author.username if post.author else 'AVEX'
    raw_content = post.content or ''
    og_title = f"{author} on AVEX"
    og_description = (raw_content[:160] + '...') if len(raw_content) > 160 else raw_content
    og_description = og_description or 'Check out this post on AVEX Alumni Network.'

    # Pick first image, or avatar, or fallback
    og_image = ''
    if hasattr(post, 'images') and post.images:
        try:
            import json
            imgs = json.loads(post.images) if isinstance(post.images, str) else post.images
            if imgs:
                og_image = request.build_absolute_uri(imgs[0])
        except Exception:
            pass
    if not og_image and post.image:
        og_image = request.build_absolute_uri(post.image.url if hasattr(post.image, 'url') else str(post.image))
    if not og_image and post.author and hasattr(post.author, 'profile') and post.author.profile.avatar:
        og_image = request.build_absolute_uri(post.author.profile.avatar.url)
    if not og_image:
        og_image = request.build_absolute_uri('/static/avex-og-default.png')

    og_url = request.build_absolute_uri()

    return render(request, 'post.html', {
        'og_title':       html_module.escape(og_title),
        'og_description': html_module.escape(og_description),
        'og_image':       og_image,
        'og_url':         og_url,
        'post_id':        post_id,
    })


class PublicPostDetailView(generics.RetrieveAPIView):
    """Public API endpoint — no auth required. Returns a single published post."""
    serializer_class = PostSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Post.objects.filter(is_published=True)

    def get_object(self):
        from django.shortcuts import get_object_or_404
        return get_object_or_404(Post, id=self.kwargs['pk'], is_published=True)


@api_view(['POST'])
def track_view(request, post_id):
    PostView.objects.create(
        user=request.user if request.user.is_authenticated else None,
        post_id=post_id
    )
    analytics, _ = PostAnalytics.objects.get_or_create(post_id=post_id)
    analytics.views += 1
    analytics.save()
    return Response({'status': 'recorded'})
