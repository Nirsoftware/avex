from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    summary = models.TextField(blank=True)
    about = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    banner = models.ImageField(upload_to='banners/', null=True, blank=True)
    cv = models.FileField(upload_to='cvs/', null=True, blank=True)

    def __str__(self):
        return self.user.username


class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following_relations')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers_relations')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


class Experience(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='experiences')
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.title} at {self.company}"


class Education(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='educations')
    degree = models.CharField(max_length=255)
    field = models.CharField(max_length=255)
    school = models.CharField(max_length=255)
    start_year = models.IntegerField()
    end_year = models.IntegerField()
    info = models.TextField(blank=True)

    def __str__(self):
        return f"{self.degree} - {self.school}"


class Skill(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=100)
    endorsements = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class Recommendation(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='recommendations')
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    text = models.TextField()

    def __str__(self):
        return self.name


class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField()
    image = models.ImageField(upload_to='posts/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Post by {self.author.username}"