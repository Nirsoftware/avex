# jobs/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from profiles.models import Profile
from .models import Job, JobApplication, JobComment, JobRecommendation
from .forms import JobApplicationForm, JobForm

# DRF imports
from rest_framework import generics
from .serializers import (
    JobSerializer,
    JobApplicationSerializer,
    JobCommentSerializer,
    JobRecommendationSerializer,
)

# ------------------------------
# Regular HTML Views
# ------------------------------

def get_jobs_context(request):
    query = request.GET.get('search')
    category = request.GET.get('category')
    location = request.GET.get('location')
    level = request.GET.get('level')

    jobs = Job.objects.all().order_by('-posted_date')

    if query:
        jobs = jobs.filter(
            Q(title__icontains=query)
            | Q(company__icontains=query)
            | Q(description__icontains=query)
            | Q(requirements__icontains=query)
        )
    if category:
        jobs = jobs.filter(category__iexact=category)
    if location:
        jobs = jobs.filter(location__icontains=location)
    if level:
        jobs = jobs.filter(level__iexact=level)

    profile = None
    profile_obj = Profile.objects.filter(user=request.user).first() if request.user.is_authenticated else None
    if profile_obj:
        profile = profile_obj

    job_cards = []
    for job in jobs:
        job_cards.append({
            'job': job,
            'fit_score': job.fit_score(profile),
            'is_owner': request.user.is_authenticated and job.owner == request.user,
            'recommended': request.user.is_authenticated and job.recommendations.filter(user=request.user).exists(),
            'recommend_count': job.recommendations.count(),
            'accepting_applications': job.accepting_applications,
        })

    return {
        'jobs': jobs,
        'job_cards': job_cards,
        'profile': profile,
        'search_value': query or '',
        'filter_category': category or '',
        'filter_location': location or '',
        'filter_level': level or '',
    }


@login_required
def job_list(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.warning(request, 'You must be logged in to post a job.')
            return redirect('login')
        job_form = JobForm(request.POST)
        if job_form.is_valid():
            new_job = job_form.save(commit=False)
            new_job.owner = request.user
            new_job.save()
            messages.success(request, 'Job posted successfully.')
            return redirect('/jobs/')
    else:
        job_form = JobForm()

    context = get_jobs_context(request)
    context['job_form'] = job_form
    return render(request, 'jobs.html', context)


def job_detail(request, id):
    job = get_object_or_404(Job, id=id)
    return render(request, 'jobs.html', {'job': job})


@login_required
def apply_job(request, id):
    job = get_object_or_404(Job, id=id)

    if request.method == 'POST':
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.save()
            messages.success(request, 'Your application has been submitted.')
            return redirect('/jobs/')
    else:
        form = JobApplicationForm()

    return render(request, 'jobs.html', {'form': form, 'job': job})


@login_required
def edit_job(request, id):
    job = get_object_or_404(Job, id=id)
    if job.owner != request.user:
        messages.error(request, 'You are not authorized to edit this job.')
        return redirect('/jobs/')

    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, 'Job updated successfully.')
            return redirect('/jobs/')
    else:
        form = JobForm(instance=job)

    context = get_jobs_context(request)
    context.update({'job_form': form, 'editing': True, 'job': job})
    return render(request, 'jobs.html', context)


@login_required
def delete_job(request, id):
    job = get_object_or_404(Job, id=id)
    if job.owner != request.user:
        messages.error(request, 'You are not authorized to delete this job.')
        return redirect('/jobs/')

    if request.method == 'POST':
        job.delete()
        messages.success(request, 'Job deleted successfully.')
        return redirect('/jobs/')

    return render(request, 'jobs.html', {'confirm_delete': True, 'job': job})


@login_required
def recommend_job(request, id):
    job = get_object_or_404(Job, id=id)

    if job.owner == request.user:
        messages.warning(request, 'You cannot recommend your own job.')
        return redirect('/jobs/')

    existing = JobRecommendation.objects.filter(job=job, user=request.user).first()
    if existing:
        existing.delete()
        messages.success(request, 'You removed your recommendation for this job.')
    else:
        JobRecommendation.objects.create(job=job, user=request.user)
        messages.success(request, 'You recommended this job.')

    return redirect('/jobs/')


@login_required
def toggle_accepting_job(request, id):
    job = get_object_or_404(Job, id=id)
    if job.owner != request.user:
        messages.error(request, 'You are not authorized to change job application status.')
        return redirect('/jobs/')

    job.accepting_applications = not job.accepting_applications
    job.save()
    state = 'accepting now' if job.accepting_applications else 'not accepting applications'
    messages.success(request, f'Job is now {state}.')
    return redirect('/jobs/')


# ------------------------------
# API Views
# ------------------------------

class JobListAPI(generics.ListCreateAPIView):
    queryset = Job.objects.all().order_by('-posted_date')
    serializer_class = JobSerializer


class JobDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer


class JobApplicationAPI(generics.CreateAPIView):
    queryset = JobApplication.objects.all()
    serializer_class = JobApplicationSerializer


class JobCommentListCreateAPI(generics.ListCreateAPIView):
    """
    List comments for a job or create a new one.
    Use: /api/job-comments/?job=<job_id>
    """
    queryset = JobComment.objects.all().order_by("-created_at")
    serializer_class = JobCommentSerializer

    def get_queryset(self):  # sourcery skip: use-named-expression
        qs = super().get_queryset()
        job_id = self.request.query_params.get("job")
        if job_id:
            qs = qs.filter(job_id=job_id)
        return qs


class JobRecommendationListCreateAPI(generics.ListCreateAPIView):
    """
    List or create recommendations.
    """
    queryset = JobRecommendation.objects.all().order_by("-created_at")
    serializer_class = JobRecommendationSerializer