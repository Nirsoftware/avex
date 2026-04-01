from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feed_posts')
    content = models.TextField(blank=True)
    image = models.ImageField(upload_to='posts/images/', null=True, blank=True)
    video = models.FileField(upload_to='posts/videos/', null=True, blank=True)
    link = models.URLField(null=True, blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    original_post = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='reposts'
    )

    def __str__(self):
        return f"Post by {self.author.username}: {self.content[:50]}"


class Comment(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author.username} on post {self.post.id}"


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'content_type', 'object_id')

    def __str__(self):
        return f"Like by {self.user.username}"


class Repost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reposts')
    original_post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reshares')
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Repost by {self.user.username} of post {self.original_post.id}"


class PostAnalytics(models.Model):
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='analytics')
    views = models.PositiveIntegerField(default=0)
    reach = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Analytics for post {self.post.id}"


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('repost', 'Repost'),
        ('reply', 'Reply'),
        ('post', 'Post'),
    ]
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    target_url = models.CharField(max_length=400, blank=True)
    extra_data = models.JSONField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_text(self):
        if self.notification_type == 'post' and self.post:
            snippet = self.post.content.strip().split()[:4]
            snippet_text = ' '.join(snippet)
            if len(self.post.content.strip().split()) > 4:
                snippet_text += '...'
            return f"{self.sender.username} has posted '{snippet_text}'"

        if self.notification_type == 'like' and self.post:
            return f"{self.sender.username} liked your post"
        if self.notification_type == 'comment' and self.post:
            return f"{self.sender.username} commented on your post"
        if self.notification_type == 'repost' and self.post:
            return f"{self.sender.username} reposted your post"
        if self.notification_type == 'reply' and self.post:
            return f"{self.sender.username} replied to your comment"

        return f"{self.sender.username} performed {self.notification_type}"

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.notification_type}"


class PostView(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='views')
    viewed_at = models.DateTimeField(auto_now_add=True)
