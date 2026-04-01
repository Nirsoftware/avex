# jobs/forms.py
from django import forms
from .models import JobApplication, Job

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'company', 'location', 'contact_email', 'job_type', 'category', 'level', 'description', 'requirements', 'salary', 'featured']
        labels = {
            'title': 'Job Title',
            'company': 'Company Name',
            'location': 'Location',
            'contact_email': 'Contact Email',
            'job_type': 'Job Type',
            'category': 'Category',
            'level': 'Experience Level',
            'description': 'Job Description',
            'requirements': 'Key Requirements',
            'salary': 'Salary Range (Optional)',
            'featured': 'Featured Listing',
        }
        help_texts = {
            'description': 'Share the role purpose, responsibilities and day-to-day activities.',
            'requirements': 'List the must-have qualifications and skills, one per line.',
            'salary': 'Optional: e.g., "NGN 500k - 700k per month".',
            'contact_email': 'Use the email candidates should send applications to.',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Senior Backend Engineer'}),
            'company': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., TechCore Solutions'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Lagos, Nigeria'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'recruiter@company.com'}),
            'job_type': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'level': forms.Select(attrs={'class': 'form-control'}),
            'salary': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., UGX 5M - 8M / mo'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe the opportunity, responsibilities, and team culture.'}),
            'requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'List key requirements (one per line).'}),
            'featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ['name', 'email', 'resume', 'cover_letter']
        widgets = {
            'cover_letter': forms.Textarea(attrs={'rows': 4}),
        }