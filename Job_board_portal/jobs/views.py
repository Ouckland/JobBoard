from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db import IntegrityError
from django.template import engines

from django.db.models import Q, Count, Case, When, IntegerField, Value
from django.utils import timezone

from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import Http404, HttpResponseNotFound, HttpResponseForbidden
from .models import JobApplication, JobPosting, Notification, JobType, Status, SavedJob, JobStatus, ApplicationReview
from .forms import PostJobForm, ApplyForJobForm
from django.utils import timezone
from users.models import EmployerProfile, SeekerProfile
from .utils import get_user_profile, create_notification
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt



User = get_user_model()

# Create your views here.

def home(request):
    return render(request, 'app/home.html')

@login_required
def dashboard(request):
    user = request.user
    profile, profile_type = get_user_profile(user)

    if profile is None:
        messages.error(request, "No profile found. Please complete your profile setup.")
        return redirect('users:choose_account_type')

    context = {'profile_type': profile_type}

    if profile_type == 'employer':
        # Active jobs (not expired)
        active_jobs = JobPosting.objects.filter(
            employer=profile,
            deadline__gte=timezone.now().date(),
            job_status='open'
        ).order_by('-posted_date')
        
        # Recent applications (last 7 days)
        one_week_ago = timezone.now() - timezone.timedelta(days=7)
        recent_applications = JobApplication.objects.filter(
            job__employer=profile,
            application_date__gte=one_week_ago
        ).select_related('applicant', 'job').order_by('-application_date')[:5]
        
        # Dashboard statistics
        total_jobs_posted = JobPosting.objects.filter(employer=profile).count()
        total_applications = JobApplication.objects.filter(job__employer=profile).count()
        closed_jobs = JobPosting.objects.filter(
            employer=profile,
            deadline__lt=timezone.now().date()
        ).count()
        
        # Popular jobs (most applications)
        popular_jobs = JobPosting.objects.filter(
            employer=profile
        ).annotate(
            application_count=Count('applications')
        ).order_by('-application_count')[:3]
        
        context.update({
            'active_jobs': active_jobs,
            'recent_applications': recent_applications,
            'total_jobs_posted': total_jobs_posted,
            'total_applications': total_applications,
            'closed_jobs': closed_jobs,
            'popular_jobs': popular_jobs,
        })

    elif profile_type == 'seeker':
        # Base queryset - all active jobs not applied to by this seeker
        jobs = JobPosting.objects.filter(
            deadline__gte=timezone.now().date(),
            job_status='open'
        ).exclude(applications__applicant=profile)

        # --- Search & Filter Functionality ---
        search_query = request.GET.get('q')
        job_type = request.GET.get('job_type')
        location = request.GET.get('location')
        
        if search_query:
            jobs = jobs.filter(
                Q(title__icontains=search_query) |
                Q(qualifications__icontains=search_query) |
                Q(skills_required__icontains=search_query) |
                Q(employer__company_name__icontains=search_query)
            )
        
        if job_type:
            jobs = jobs.filter(job_type=job_type)
        
        if location:
            jobs = jobs.filter(location__icontains=location)

        # Store search parameters in context
        context['search_query'] = search_query
        context['selected_job_type'] = job_type
        context['selected_location'] = location

        # --- DEBUG: Check what we have before recommendations ---
        print(f"Total jobs after filters: {jobs.count()}")
        print(f"Seeker skills: {profile.skills}")

        # --- Recommended Jobs ---
        recommended_jobs = []
        
        # In your dashboard view, update the recommendation logic:
        if profile.skills and jobs.exists():
            seeker_skills = [s.strip().lower() for s in profile.skills.split(",") if s.strip()]
            
            jobs_with_scores = []
            for job in jobs:
                if job.skills_required:
                    job_skills = [s.strip().lower() for s in job.skills_required.split(",") if s.strip()]
                    
                    # Calculate matches
                    matched_skills = list(set(seeker_skills) & set(job_skills))
                    missing_skills = list(set(job_skills) - set(seeker_skills))
                    match_count = len(matched_skills)
                    
                    # Calculate percentage match
                    if job_skills:
                        percent_match = int((match_count / len(job_skills)) * 100)
                    else:
                        percent_match = 0
                    
                    # Determine match quality
                    if percent_match >= 80:
                        match_quality = "excellent"
                    elif percent_match >= 60:
                        match_quality = "good"
                    elif percent_match >= 40:
                        match_quality = "fair"
                    else:
                        match_quality = "weak"
                    
                    # Attach all match data to job object
                    job.match_score = percent_match
                    job.match_quality = match_quality
                    job.matched_skills = matched_skills
                    job.missing_skills = missing_skills
                    job.total_skills_required = len(job_skills)
                    
                    jobs_with_scores.append((job, percent_match))
            
            # Sort by match score
            jobs_with_scores.sort(key=lambda x: (x[1], x[0].posted_date), reverse=True)
            recommended_jobs = [job for job, score in jobs_with_scores]
        
        # Fallback: if no skills or no matches, show popular jobs
        if not recommended_jobs:
            print("Using fallback: popular jobs")
            recommended_jobs = jobs.annotate(
                application_count=Count('applications')
            ).order_by('-application_count', '-posted_date')[:10]
        
        # Check saved status for all recommended jobs
        saved_job_ids = SavedJob.objects.filter(
            job_saver=profile,
            job__in=recommended_jobs
        ).values_list('job_id', flat=True)
        context['saved_job_ids'] = list(saved_job_ids)

        # Pagination for search results
        paginator = Paginator(jobs, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context.update({
            'recommended_jobs': recommended_jobs[:10],  # Limit to 10 recommendations
            'latest_jobs': page_obj,
            'job_types': JobType.choices,
            'job_applications': JobApplication.objects.filter(
                applicant=profile
            ).select_related('job', 'job__employer').order_by('-application_date')[:5]
        })

    return render(request, 'app/dashboard.html', context)




@login_required
def add_job(request):
    user = request.user

    try:
        profile = user.employerprofile
    except EmployerProfile.DoesNotExist:
        messages.error(request, 'This action is only allowed for employer accounts.')
        return redirect('jobs:forbidden')

    if request.method == 'POST':
        form = PostJobForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                job = form.save(commit=False)
                job.job_status = JobStatus.open
                job.employer = profile
                job.save()
                create_notification(
                    recipient=request.user,
                    message=f'The job {job.title} has been posted succesfully!',
                )
                messages.success(request, 'Job successfully posted.')
                return redirect('jobs:dashboard')
            except IntegrityError:
                messages.error(request, 'There was an error saving the job. Please try again.')
    else:
        form = PostJobForm()

    return render(request, 'app/employer/add-job.html', {'job_form': form})


@login_required
def view_job_detail(request, job_id):
    user = request.user

    try:
        job = get_object_or_404(JobPosting, id=job_id)

        # Optional: Ensure only the employer who posted the job can view its detail
        if hasattr(user, 'employerprofile') and job.employer != user.employerprofile:
            messages.error(request, 'Access denied: You are not authorized to view this job.')
            return redirect('jobs:dashboard')

    except JobPosting.DoesNotExist:
        messages.error(request, 'Job not found.')
        return redirect('jobs:dashboard')

    context = {
        'job': job,
    }
    return render(request, 'app/employer/view-job-detail.html', context)



@login_required
def update_job_details(request, job_id):
    user = request.user

    if not user:
        messages.error(request, 'Session has expired. Try logging in again.')
        return redirect('users:login')

    job = get_object_or_404(JobPosting, id=job_id)
    applications = JobApplication.objects.filter(job=job)

    if job.employer != user.employerprofile:
        messages.error(request, 'You are not authorized to edit this job.')
        return redirect('jobs:dashboard')

    if request.method == 'POST':
        form = PostJobForm(request.POST, request.FILES, instance=job)
        if form.is_valid():
            try:
                form.save()
                
                # Notify the employer
                create_notification(
                    recipient=request.user,
                    message=f"Job details for '{job.title}' have been updated successfully.",
                )

                # Notify each applicant
                for application in applications:
                    try:
                        link = reverse('jobs:update_application', args=[application.id])
                        create_notification(
                            recipient=application.applicant.user,
                            message=(
                                f"The job '{job.title}' you applied for at {job.employer} has been updated. "
                                "Please review and update your application if needed."
                            ),
                            url=link,
                        )
                    except Exception as e:
                        messages.error(request, f"Notification error for applicant {application.applicant}: {e}")

                messages.success(request, 'Job details updated successfully.')
                return redirect('jobs:dashboard')

            except IntegrityError:
                messages.error(request, 'An error occurred while saving the job. Please try again.')

    else:
        form = PostJobForm(instance=job)

    context = {
        'job': job,
        'job_form': form,
    }

    return render(request, 'app/employer/update-job-details.html', context)


@login_required
def delete_job(request, job_id):
    user = request.user

    if not user:
        messages.error(request, 'Session has expired. Try logging in again.')
        return redirect('users:login')

    job = get_object_or_404(JobPosting, id=job_id)

    # Check permission
    if job.employer != user.employerprofile:
        messages.error(request, 'You do not have permission to delete this job.')
        return redirect('jobs:dashboard')

    # Save job info before deletion
    job_title = job.title
    employer_name = str(job.employer)

    # Get all applications before job is deleted
    applications = job.applications.select_related('applicant__user').all()
        # Delete the job
    if request.method == 'POST':
        job.delete()

        # Notify employer
        create_notification(
            recipient=request.user,
            message=f'Your job "{job_title}" has been successfully deleted.'
        )

        # Notify all applicants
        for application in applications:
            print(f"Sending to {application.applicant.user} for job {job_title}")
            try:
                create_notification(
                    recipient=application.applicant.user,
                    message=f'The job "{job_title}" at {employer_name} you applied for has been removed by the employer.'
                )
            except Exception as e:
                messages.error(request, f"Notification error for applicant {application.applicant}: {e}")

        messages.success(request, 'Job successfully deleted.')
        return redirect('jobs:dashboard')

    return render(request, 'app/employer/delete-job.html', {'job': job})




@login_required
def apply_for_job(request, job_id):
    user = request.user

    if not user:
        messages.error(request, 'Session has expired. Try logging in again.')
        return redirect('users:login')

    job = get_object_or_404(JobPosting, id=job_id)

    try:
        seeker = user.seekerprofile
    except SeekerProfile.DoesNotExist:
        messages.error(request, 'You must have a seeker profile to apply for jobs.')
        return redirect('jobs:dashboard')

    # Check if already applied
    if JobApplication.objects.filter(job=job, applicant=seeker).exists():
        messages.warning(request, 'You have already applied for this job.')
        return redirect('jobs:view_job_detail', job_id=job_id)

    form = ApplyForJobForm(request.POST or None, request.FILES or None)

    if request.method == 'POST':
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = seeker
            application.save()

            create_notification(
                recipient=application.applicant.user,
                message=f"Your application for the role {application.job.title} at {application.job.employer.company_name} has been submtted succesfully",
                url=reverse('jobs:view_application_detail', args=[application.id])
            )
            try:
                create_notification(
                    recipient=application.job.employer.user,
                    message=f"{application.applicant.full_name} has applied for the job {application.job.title}",
                    url=reverse("jobs:view_application_detail", args=[application.id])
                )
            except Exception as e:
                messages.error(request, str(e))
                
            messages.success(request, 'Application submitted successfully.')
            return redirect('jobs:dashboard')
        

    context = {
        'job': job,
        'form': form,
    }
    return render(request, 'app/seeker/apply-for-job.html', context)



@login_required
def view_application_detail(request, application_id):
    user = request.user
    application = get_object_or_404(JobApplication.objects.select_related('job', 'applicant__user', 'job__employer'), id=application_id)

    is_seeker = hasattr(user, 'seekerprofile') and application.applicant == user.seekerprofile
    is_employer = hasattr(user, 'employerprofile') and application.job.employer == user.employerprofile

    if not (is_seeker or is_employer):
        messages.error(request, 'You are not authorized to access this application.')
        return redirect('jobs:dashboard')

    context = {
        'application': application,
        'is_seeker': is_seeker,
        'is_employer': is_employer,
    }
    return render(request, 'app/seeker/view-application-detail.html', context)


@login_required
def review_application(request, application_id):
    application = get_object_or_404(JobApplication, id=application_id)
    
    if application.job.employer != request.user.employerprofile:
        messages.error(request, "Not authorized.")
        return redirect('jobs:dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'accept':
            # Redirect to email composition for acceptance
            return redirect('jobs:compose_acceptance_email', application_id=application.id)
            
        elif action == 'reject':
            application.status = 'rejected'
            application.save()
            messages.success(request, 'Application rejected.')
            
        return redirect('jobs:view_applications', job_id=application.job.id)

    return render(request, 'app/employer/review-application.html', {
        'application': application,
    })


@login_required
def compose_acceptance_email(request, application_id):
    application = get_object_or_404(JobApplication, id=application_id)
    
    if application.job.employer != request.user.employerprofile:
        messages.error(request, "Not authorized.")
        return redirect('jobs:dashboard')
    
    # Prevent reviewing already reviewed applications
    if application.status != 'pending':
        messages.error(request, "Application already reviewed.")
        return redirect('jobs:view_applications', job_id=application.job.id)

    context = {
        'candidate_name': application.applicant.full_name,
        'job_title': application.job.title,
        'company_name': application.job.employer.company_name,
    }

    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        message_content = request.POST.get('message', '').strip()

        if not subject or not message_content:
            messages.error(request, 'Subject and message are required.')
            return render(request, 'app/employer/compose-acceptance-email.html', {
                'application': application,
                'subject': subject,
                'message': message_content,
                **context
            })

        try:
            # Replace template variables
            final_subject = subject.replace('{candidate_name}', context['candidate_name'])
            final_message = message_content.replace('{candidate_name}', context['candidate_name'])
            final_message = final_message.replace('{job_title}', context['job_title'])
            final_message = final_message.replace('{company_name}', context['company_name'])

            # Send email
            send_mail(
                final_subject,
                final_message,
                settings.DEFAULT_FROM_EMAIL,
                [application.applicant.user.email],
                fail_silently=False,
            )

            # Update application status to 'accepted'
            application.status = 'accepted'
            application_review = ApplicationReview.objects.create(
                application=application,
                reviewer=application.job.employer
            )
            
            application_review.save()
            application.save()

            # Notify applicant
            create_notification(
                recipient=application.applicant.user,
                message=f"Your application for {application.job.title} was accepted! Check your email for details.",
                url=reverse("jobs:view_application_detail", args=[application.id]),
            )

            messages.success(request, 'Acceptance email sent successfully!')
            return redirect('jobs:view_applications', job_id=application.job.id)

        except Exception as e:
            messages.error(request, f'Error sending email: {str(e)}')
            return render(request, 'app/employer/compose-acceptance-email.html', {
                'application': application,
                'subject': subject,
                'message': message_content,
                **context
            })

    else:
        # GET request - EMPTY FORM (no default messaging)
        return render(request, 'app/employer/compose-acceptance-email.html', {
            'application': application,
            'subject': '',  # Empty subject
            'message': '',  # Empty message
            **context
        })

    
def send_acceptance_email(application):
    subject = f'Your application for {application.job.title} at {application.job.employer.company_name}'
    message = (
        f'Dear {application.applicant.full_name},\n\n'
        f'We are pleased to inform you that your application for the position of {application.job.title} at {application.job.employer.company_name} has been accepted.\n\n'
        'Please reply to this email to discuss the next steps.\n\n'
        'Best regards,\n'
        f'{application.job.employer.company_name}'
    )
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [application.applicant.user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f'Error sending acceptance email: {e}')
        return False

@login_required
def view_applications(request, job_id):
    job = get_object_or_404(JobPosting, id=job_id, employer=request.user.employerprofile)
    applications = job.applications.select_related('applicant__user').all()
    return render(request, 'app/employer/view-applications.html', {
        'job': job,
        'applications': applications,
    })

@login_required
def view_applications(request, job_id):
    job = get_object_or_404(JobPosting, id=job_id, employer=request.user.employerprofile)
    applications = job.applications.select_related('applicant__user').all()
    
    # Calculate real statistics
    total_applications = applications.count()
    pending_count = applications.filter(status='pending').count()
    shortlisted_count = applications.filter(status='shortlisted').count()
    interview_count = applications.filter(status='interview').count()
    offer_count = applications.filter(status='offer').count()
    hired_count = applications.filter(status='hired').count()
    rejected_count = applications.filter(status='rejected').count()
    
    return render(request, 'app/employer/view-applications.html', {
        'job': job,
        'applications': applications,
        'total_applications': total_applications,
        'pending_count': pending_count,
        'shortlisted_count': shortlisted_count,
        'interview_count': interview_count,
        'offer_count': offer_count,
        'hired_count': hired_count,
        'rejected_count': rejected_count,
    })


@login_required
def delete_application(request, application_id):
    user = request.user

    if not user:
        messages.error(request, 'Session has expired. Try logging in again.')
        return redirect('users:login')

    application = get_object_or_404(JobApplication, id=application_id)

    # Ensure the user is the owner of the application
    if application.applicant.user != user:
        messages.error(request, 'You are not authorized to delete this application.')
        return redirect('jobs:dashboard')
 
    job_role = application.job.title
    employer = application.job.employer
    applicant = application.applicant.full_name

    if request.method == 'POST':
        application.delete()

        create_notification(
            recipient=request.user,
            message=f'You have deleted your application for the job role {job_role} at {employer.company_name}'
        )
        try:
            create_notification(
                recipient=employer.user,
                message=f'Applicant {applicant} have deleted their application for the job role {job_role} you posted.'
            )
        except Exception as e:
            messages.error(request, str(e))

        messages.success(request, 'Job application deleted successfully.')
        return redirect('jobs:dashboard')

    context = {
        'application': application,
    }

    return render(request, 'app/seeker/delete-application.html', context)




@login_required
def update_application(request, application_id):
    user = request.user
    application = get_object_or_404(JobApplication, id=application_id)

    # Only the applicant can update their own application
    if application.applicant.user != user:
        messages.error(request, 'You are not authorized to edit this application.')
        return redirect('jobs:dashboard')

    # Prevent editing if status is not pending
    if application.status != 'pending':
        messages.warning(request, 'You cannot edit an application that has already been reviewed.')
        return redirect('jobs:view_application_detail', application_id=application.id)

    if request.method == 'POST':
        form = ApplyForJobForm(request.POST, request.FILES, instance=application)
        if form.is_valid():
            form.save()

            # Notify seeker
            create_notification(
                recipient=user,
                message=f'You have successfully updated your application for the role "{application.job.title}" at {application.job.employer.company_name}.',
                url=reverse('jobs:view_application_detail', args=[application.id]),
            )

            # Notify employer
            create_notification(
                recipient=application.job.employer.user,
                message=f'Applicant {application.applicant.full_name} updated their application for your job "{application.job.title}".',
                url=reverse('jobs:view_applications', args=[application.job.id]),
            )

            messages.success(request, 'Job application updated successfully.')
            return redirect('jobs:view_application_detail', application_id=application.id)
    else:
        form = ApplyForJobForm(instance=application)

    return render(request, 'app/seeker/update-application.html', {
        'application': application,
        'form': form,
    })

def forbidden(request):
    return render(request, 'error-pages/forbidden.html', )


@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()
    return render(request, 'app/notifications.html', {
        'notifications': notifications,
        'unread_count': unread_count
    })


@login_required
def mark_notification_as_read(request, notification_id):
    if request.method == 'POST':
        notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
        if not notification.is_read:
            notification.is_read = True
            notification.save()
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return JsonResponse({'success': True, 'unread_count': unread_count})
    return JsonResponse({'success': False}, status=400)


@login_required
def mark_all_as_read(request):
    if request.method == 'POST':
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'success': True, 'unread_count': 0})
    return JsonResponse({'success': False}, status=400)



def all_jobs(request):
    user = request.user
    if not user or user is None:
        messages.error(request, 'Session expired. Please log in again.')
        return redirect('users:login')

    profile, profile_type = get_user_profile(user)
    if profile is None:
        messages.error(request, 'Profile not found. Please complete your profile.')
        return redirect('users:profile_setup')

    context = {}
    
    if profile_type == 'employer':
        # Existing employer logic (unchanged)
        all_jobs = JobPosting.objects.filter(employer=user.employerprofile).order_by('-posted_date')
        all_jobs = JobPosting.objects.filter(employer=user.employerprofile).order_by('-posted_date')
        
        # Get search query
        search_query = request.GET.get('q', '')
        
        # Get filters from URL parameters
        location = request.GET.get('location', '')
        job_type = request.GET.get('type', '')
        salary_min = request.GET.get('salary_min', '')
        salary_max = request.GET.get('salary_max', '')
        
        # Apply filters
        if search_query:
            all_jobs = all_jobs.filter(
                Q(title__icontains=search_query) |
                Q(location__icontains=search_query) |
                Q(skills_required__icontains=search_query)
            )
        
        if location:
            all_jobs = all_jobs.filter(location__icontains=location)
        
        if job_type:
            all_jobs = all_jobs.filter(job_type=job_type)
        
        if salary_min:
            all_jobs = all_jobs.filter(salary__gte=salary_min)
        
        if salary_max:
            all_jobs = all_jobs.filter(salary__lte=salary_max)
        
        # Pagination
        paginator = Paginator(all_jobs, 10)  # Show 10 jobs per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'profile_type': profile_type,
            'jobs': page_obj,
            'search_query': search_query,
            'location': location,
            'job_type': job_type,
            'salary_min': salary_min,
            'salary_max': salary_max,
            'job_types': JobType.choices,  # Assuming you have this in your model
        }

    elif profile_type == 'seeker':
        # Base queryset: active jobs not applied to by seeker
        all_jobs = JobPosting.objects.filter(
            deadline__gte=timezone.now().date()
        ).exclude(applications__applicant=profile).order_by('-posted_date')


        # --- Search & Filters ---
        search_query = request.GET.get('q', '')
        location = request.GET.get('location', '')
        job_type = request.GET.get('type', '')
        salary_min = request.GET.get('salary_min', '')
        salary_max = request.GET.get('salary_max', '')

        if search_query:
            all_jobs = all_jobs.filter(
                Q(title__icontains=search_query) |
                Q(location__icontains=search_query) |
                Q(skills_required__icontains=search_query) |
                Q(employer__company_name__icontains=search_query)
            )

        if location:
            all_jobs = all_jobs.filter(location__icontains=location)

        if job_type:
            all_jobs = all_jobs.filter(job_type=job_type)

        if salary_min:
            all_jobs = all_jobs.filter(salary__gte=salary_min)

        if salary_max:
            all_jobs = all_jobs.filter(salary__lte=salary_max)

        # --- Skill-Based Recommendations
        recommended_jobs = None
        if profile.skills:
            seeker_skills = set(s.strip().lower() for s in profile.skills.split(",") if s.strip())
            jobs_with_scores = []
            for job in all_jobs:
                job_skills = set(s.strip().lower() for s in job.skills_required.split(",") if s.strip())
                matches = seeker_skills & job_skills
                match_score = len(matches)
                # Calculate percent match (avoid division by zero)
                percent_match = int(100 * match_score / max(len(job_skills), 1))
                job.match_score = percent_match  # Attach to job object
                jobs_with_scores.append((job, percent_match))
            # Sort jobs by percent_match and posted_date
            jobs_with_scores.sort(key=lambda x: (x[1], x[0].posted_date), reverse=True)
            recommended_jobs = [job for job, score in jobs_with_scores if score > 0]
        else:
            recommended_jobs = all_jobs.annotate(
            application_count=Count('applications')
            ).order_by('-application_count', '-posted_date')



        saved_job_ids = SavedJob.objects.filter(
            job_saver=profile,
            job__in=recommended_jobs
            ).values_list('job_id', flat=True)




        # Pagination
        paginator = Paginator(all_jobs, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
    
            'jobs': page_obj,
            'recommended_jobs': recommended_jobs,
            'search_query': search_query,
            'location': location,
            'job_type': job_type,
            'salary_min': salary_min,
            'salary_max': salary_max,
            'job_types': JobType.choices,
            'profile_type': profile_type,
            'saved_job_ids': list(saved_job_ids) if recommended_jobs else [],
        }

    else:
        messages.error(request, 'Invalid profile type.')
        return redirect('users:profile_setup')

    return render(request, 'app/all-jobs.html', context)





def all_applications(request):
    user = request.user
    if not user or user is None:
        messages.error(request, 'Sesion expired, Please try to log in again')
        return redirect('users:login')
    job = JobPosting.objects.filter(employer=user.employerprofile)
    applications = JobApplication.objects.get(job.employer==user.employerprofile)
    
 



def all_applications(request):
    user = request.user
    if not user or not user.is_authenticated:
        messages.error(request, 'Session expired. Please log in again.')
        return redirect('users:login')

    profile, profile_type = get_user_profile(user)

    applications = JobApplication.objects.all()

    context = {}

    if profile_type == 'employer':
        applications = applications.filter(job__employer=user.employerprofile).order_by('-application_date')

        # Employer-specific filters
        search_query = request.GET.get('q', '')
        applicant_name = request.GET.get('applicant', '')
        application_date = request.GET.get('application_date', '')
        status = request.GET.get('status', '')
        job_title = request.GET.get('job_title', '')

        if search_query:
            applications = applications.filter(
                Q(applicant__user__username__icontains=search_query) |
                Q(cover_letter__icontains=search_query) |
                Q(job__title__icontains=search_query)
            )
        if applicant_name:
            applications = applications.filter(
                Q(applicant__full_name__icontains=applicant_name) |
                Q(applicant__user__first_name__icontains=applicant_name) |
                Q(applicant__user__last_name__icontains=applicant_name)
            )
        if application_date:
            try:
                date_obj = datetime.strptime(application_date, '%Y-%m-%d').date()
                applications = applications.filter(application_date__date=date_obj)
            except ValueError:
                pass
        if status:
            applications = applications.filter(status=status)
        if job_title:
            applications = applications.filter(job__title__icontains=job_title)

        context.update({
            'search_query': search_query,
            'applicant_name': applicant_name,
            'application_date': application_date,
            'status': status,
            'job_title': job_title,
            'status_choices': Status.choices,
        })

    elif profile_type == 'seeker':
        applications = applications.filter(applicant=user.seekerprofile).select_related('job').order_by('-application_date')

        # Filters
        search_query = request.GET.get('q', '')
        job_title = request.GET.get('job_title', '')
        location = request.GET.get('location', '')
        status = request.GET.get('status', '')
        application_date = request.GET.get('application_date', '')

        if search_query:
            applications = applications.filter(
                Q(job__title__icontains=search_query) |
                Q(job__location__icontains=search_query) |
                Q(job__skills_required__icontains=search_query)
            )

        if job_title:
            applications = applications.filter(job__title__icontains=job_title)

        if location:
            applications = applications.filter(job__location__icontains=location)

        if status:
            applications = applications.filter(status=status)

        if application_date:
            try:
                date_obj = datetime.strptime(application_date, '%Y-%m-%d').date()
                applications = applications.filter(application_date__date=date_obj)
            except ValueError:
                pass

        context.update({
            'search_query': search_query,
            'job_title': job_title,
            'location': location,
            'status': status,
            'application_date': application_date,
            'status_choices': Status.choices,
        })

    # Pagination
    paginator = Paginator(applications, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context['applications'] = page_obj
    context['profile_type'] = profile_type

    return render(request, 'app/all-applications.html', context)









@login_required
def save_job(request, job_id):
    job = get_object_or_404(JobPosting, id=job_id)
    profile, profile_type = get_user_profile(request.user)
    
    if profile_type != 'seeker':
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Only job seekers can save jobs'}, status=403)
        messages.error(request, 'Only job seekers can save jobs')
        return redirect('jobs:job_detail', job_id=job.id)
    
    if SavedJob.objects.filter(job=job, job_saver=profile).exists():
        message = 'This job is already in your saved list'
        status = 'info'
        html = render_to_string('partials/unsave_button.html', {'job': job}, request=request)
    else:
        SavedJob.objects.create(job=job, job_saver=profile)
        message = 'Job saved successfully'
        status = 'success'
        html = render_to_string('partials/unsave-job.html', {'job': job}, request=request)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': status,
            'message': message,
            'html': html
        })
    
    messages.success(request, message)
    return redirect(request.META.get('HTTP_REFERER', 'jobs:job_detail'))

@login_required
def unsave_job(request, job_id):
    job = get_object_or_404(JobPosting, id=job_id)
    profile, profile_type = get_user_profile(request.user)
    
    if profile_type != 'seeker':
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Only job seekers can unsave jobs'}, status=403)
        messages.error(request, 'Only job seekers can unsave jobs')
        return redirect('jobs:job_detail', job_id=job.id)
    
    saved_job = get_object_or_404(SavedJob, job=job, job_saver=profile)
    saved_job.delete()
    message = 'Job removed from your saved list'
    html = render_to_string('partials/save-job.html', {'job': job}, request=request)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message': message,
            'html': html
        })
    
    messages.success(request, message)
    return redirect(request.META.get('HTTP_REFERER', 'jobs:saved_jobs'))



@login_required
def saved_jobs(request):
    # Authentication and profile validation
    user = request.user
    if not user.is_authenticated:
        messages.error(request, 'Session expired. Please try logging in again')
        return redirect('users:login')
    
    profile, profile_type = get_user_profile(user)
    if profile is None:
        messages.error(request, 'Profile not found. Please complete your profile setup.')
        return redirect('users:profile_setup')
    
    if profile_type != 'seeker':
        messages.error(request, 'This page is only accessible to job seekers.')
        return redirect('jobs:dashboard')

    # Base queryset
    saved_jobs = SavedJob.objects.filter(job_saver=profile).select_related('job').order_by('-timestamp')

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        saved_jobs = saved_jobs.filter(
            Q(job__title__icontains=search_query) |
            Q(job__employer__company_name__icontains=search_query) |
            Q(job__skills_required__icontains=search_query)
        )

    # Filtering
    status_filter = request.GET.get('status')
    if status_filter:
        saved_jobs = saved_jobs.filter(job__job_status=status_filter)

    # Date filtering
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        saved_jobs = saved_jobs.filter(timestamp__gte=date_from)
    if date_to:
        saved_jobs = saved_jobs.filter(timestamp__lte=date_to)

    sort_option = request.GET.get('sort', '-timestamp')
    if sort_option in ['timestamp', '-timestamp']:
        saved_jobs = saved_jobs.order_by(sort_option)


    # Pagination
    paginator = Paginator(saved_jobs, 10)  # Show 10 jobs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'saved_jobs': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        'status_choices': JobStatus.choices,
    }

    return render(request, 'app/seeker/saved-jobs.html', context)
