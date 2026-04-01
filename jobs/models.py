# jobs/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


import re

class Job(models.Model):
    JOB_TYPE = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('internship', 'Internship'),
        ('contract', 'Contract'),
    ]

    LEVEL_CHOICES = [
        ('entry', 'Entry Level'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior Level'),
        ('executive', 'Executive'),
    ]

    CATEGORY_CHOICES = [
        ('technology', 'Technology'),
        ('finance', 'Finance'),
        ('education', 'Education'),
        ('healthcare', 'Healthcare'),
        ('business', 'Business'),
        ('engineering', 'Engineering'),
        ('other', 'Other'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jobs', null=True, blank=True)
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    description = models.TextField()
    requirements = models.TextField()
    salary = models.CharField(max_length=100, blank=True)
    contact_email = models.EmailField(blank=True)
    job_type = models.CharField(max_length=20, choices=JOB_TYPE)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='mid')
    posted_date = models.DateTimeField(auto_now_add=True)
    featured = models.BooleanField(default=False)
    accepting_applications = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    def get_keywords(self):
        text = ' '.join([self.title, self.company, self.location, self.description, self.requirements, self.category, self.level])
        words = re.findall(r"\b[\w\-]+\b", text.lower())
        return sorted(set(words))

    def fit_score(self, profile):
        if not profile:
            return None
        profile_text = ' '.join([
            profile.title or '',
            profile.location or '',
            profile.summary or '',
            profile.about or '',
            ' '.join([s.name for s in profile.skills.all()])
        ]).lower()
        if not profile_text.strip():
            return None

        keywords = self.get_keywords()
        if not keywords:
            return 0

        matched = sum(1 for kw in keywords if kw in profile_text)
        score = int((matched / len(keywords)) * 100)
        return min(100, max(0, score))


class JobApplication(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    name = models.CharField(max_length=200)
    email = models.EmailField()
    resume = models.FileField(upload_to="resumes/")
    cover_letter = models.TextField()
    applied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.job.title}"


class JobComment(models.Model):
    job = models.ForeignKey(Job, related_name="comments", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="job_comments", on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user} on {self.job}"


class JobRecommendation(models.Model):
    job = models.ForeignKey(Job, related_name="recommendations", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="job_recommendations", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("job", "user")  # prevent duplicate recommendations

    def __str__(self):
        return f"{self.user} recommended {self.job}"