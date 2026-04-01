from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = ['id', 'title', 'company', 'start_date', 'end_date', 'description']


class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = ['id', 'degree', 'field', 'school', 'start_year', 'end_year', 'info']


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name', 'endorsements']


class RecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recommendation
        fields = ['id', 'name', 'title', 'text']


class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Post
        fields = '__all__'


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    experiences = ExperienceSerializer(many=True, read_only=True)
    educations = EducationSerializer(many=True, read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    recommendations = RecommendationSerializer(many=True, read_only=True)
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    posts_count = serializers.SerializerMethodField()
    is_followed = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = '__all__'
        read_only_fields = ['user']

    def get_followers_count(self, obj):
        return obj.user.followers_relations.count()

    def get_following_count(self, obj):
        return obj.user.following_relations.count()

    def get_posts_count(self, obj):
        return obj.user.posts.count() if hasattr(obj.user, 'posts') else 0

    def get_is_followed(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.user.followers_relations.filter(follower=request.user).exists()