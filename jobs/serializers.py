# jobs/serializers.py
from rest_framework import serializers
from .models import Job, JobApplication, JobComment, JobRecommendation


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = '__all__'


class JobApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobApplication
        fields = '__all__'


class JobCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobComment
        fields = '__all__'


class JobRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobRecommendation
        fields = '__all__'