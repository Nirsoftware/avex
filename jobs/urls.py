# jobs/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # HTML views
    path("jobs/", views.job_list, name="jobs"),
    path("jobs/<int:id>/", views.job_detail, name="job_detail"),
    path("jobs/<int:id>/apply/", views.apply_job, name="apply_job"),
    path("jobs/<int:id>/edit/", views.edit_job, name="edit_job"),
    path("jobs/<int:id>/delete/", views.delete_job, name="delete_job"),
    path("jobs/<int:id>/recommend/", views.recommend_job, name="recommend_job"),
    path("jobs/<int:id>/toggle-accepting/", views.toggle_accepting_job, name="toggle_accepting_job"),

    # API views (optional, if you want them under /api/jobs/ etc.)
    path("api/jobs/", views.JobListAPI.as_view(), name="api_jobs"),
    path("api/jobs/<int:pk>/", views.JobDetailAPI.as_view(), name="api_job_detail"),
    path("api/job-applications/", views.JobApplicationAPI.as_view(), name="api_job_applications"),
]