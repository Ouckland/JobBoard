from django.shortcuts import get_object_or_404, redirect, render
from .models import JobApplication, JobPosting
from functools import wraps
from django.contrib import messages
def applicant_allowed(func):
    @wraps(func)
    def wrapper(request, application_id, *args, **kwargs):
        application = get_object_or_404(JobApplication, id=application_id)
        if request.user.seekerprofile != application.applicant:
            messages.error(request, 'You are not authorized to access this page!')
            return redirect('jobs:forbidden')
        return func(request, application, application_id, *args, **kwargs)
    return wrapper

def employer_allowed(func):
    @wraps(func)
    def wrapper(request, job_id, *args, **kwargs):
        job = get_object_or_404(JobPosting, id=job_id)
        if request.user.employerprofile != job.employer:
            messages.error(request, 'You are not authorized to access this page!')
            return redirect('jobs:forbidden')
        return func(request, job, job_id, *args, **kwargs)
    return wrapper

