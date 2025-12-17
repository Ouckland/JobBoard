from django.utils.html import format_html
from django.utils import timezone
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, MinLengthValidator
from users.models import EmployerProfile, SeekerProfile, User

# Create your models here.



class JobType(models.TextChoices):
    ft = 'FT', 'Full-Time'
    pt = 'PT', 'Part-Time'

class Status(models.TextChoices):
    pending = 'pending', 'Pending'
    accepted = 'accepted', 'Accepted' 
    rejected = 'rejected', 'Rejected'

class JobStatus(models.TextChoices):
    closed = 'closed', 'Closed'
    open = 'open', 'Open'

class JobPosting(models.Model):
    employer = models.ForeignKey(EmployerProfile, on_delete=models.CASCADE, related_name='posted_jobs')
    title = models.CharField(max_length=255, validators=[MinLengthValidator(3)])
    job_type = models.CharField(max_length=50, choices=JobType.choices, default=JobType.ft)
    location = models.CharField(max_length=255)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    experience_required = models.PositiveIntegerField(help_text='In years')
    qualifications = models.TextField()
    posted_date = models.DateTimeField(auto_now_add=True)
    deadline = models.DateField()
    job_category = models.CharField()
    job_status = models.CharField(max_length=50, choices=JobStatus.choices, default=JobStatus.open)
    skills_required = models.CharField(verbose_name="Skills Required", help_text="Enter relevant skills")


    class Meta:
        unique_together = ('employer', 'title')
        
    def is_active(self):
        return self.deadline >= timezone.now().date()
    
    def verify_job_status(self):
        if self.is_active():
            return format_html('<span style="color: green;">Open</span>')
        else:
            return format_html('<span style="color: red;">Closed</span>')

    def __str__(self):
        return f'{self.title} at {self.employer.company_name}'
    
    
class JobApplication(models.Model):
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(SeekerProfile, on_delete=models.CASCADE)
    application_date = models.DateTimeField(auto_now_add=True)
    cover_letter = models.TextField()
    resume = models.FileField(upload_to='resumes/')
    attachments = models.FileField(upload_to='attachments/', blank=True, null=True)
    status = models.CharField(max_length=14, choices=Status.choices, default=Status.pending)

    class Meta:
        unique_together = ('job', 'applicant')

    def clean(self):
        if self.job_id and self.job.deadline < timezone.now().date():
            raise ValidationError('Job application has closed.')
            

    def __str__(self):
        return f'{self.applicant.full_name} applied for {self.job.title}'




# application, reviewer, status, employer message, reviewed_at
class ApplicationReview(models.Model):
    application = models.OneToOneField(JobApplication, on_delete=models.CASCADE)
    reviewer = models.ForeignKey(EmployerProfile, on_delete=models.CASCADE)
    employer_message = models.TextField(blank=True, null=True)
    reviewed_at = models.DateTimeField(auto_now=True)    

    def __str__(self):
        return f'Review of {self.application} by {self.reviewer.company_name}'

    def get_review_status_display(self):
        return self.get_status_display()


def get_default_user():
    return User.objects.first() if User.objects.exists() else None

class SavedJob(models.Model):
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE)
    job_saver = models.ForeignKey(SeekerProfile, on_delete=models.CASCADE, default=get_default_user)
    is_saved = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['job', 'job_saver']  # Prevents duplicates

        
    def __str__(self):
        return f'{self.job.title} --- {self.job_saver.full_name}'


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    url = models.URLField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Notification to {self.recipient.username}'


