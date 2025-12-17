from django.core.files.images import get_image_dimensions
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class Country(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=5, unique=True)
    phone_code = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return f'{self.name}'
    
# models.py
class State(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('country', 'name')

    def __str__(self):
        return f"{self.name}, {self.country.name}"

class OTP(models.Model):
    user_email = models.EmailField(unique=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)

    @property
    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)

    

class Profile(models.Model):
    ACCOUNT_CHOICES = [
        ('employer', 'Employer'),
        ('seeker', 'Job Seeker'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    account_type = models.CharField(max_length=10, choices=ACCOUNT_CHOICES)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, null=True)
    state = models.ForeignKey(State, on_delete=models.CASCADE, null=True)
    

    def save(self, *args, **kwargs):
        if not self.country:
            first_country = Country.objects.first()
            if first_country:
                self.country = first_country
        super().save(*args, **kwargs)

    class Meta:
        abstract = True




COMPANY_SIZE_CHOICES = [
    ('1-10', '1-10 employees'),
    ('11-50', '11-50 employees'),
    ('51-200', '51-200 employees'),
    ('201-500', '201-500 employees'),
    ('501-1000', '501-1000 employees'),
    ('1001+', '1001+ employees'),
]


class EmployerProfile(Profile):
    company_name = models.CharField(max_length=255)
    company_website = models.URLField()
    industry = models.CharField(max_length=255)
    contact_number = models.CharField(max_length=15, blank=True)
    description = models.TextField(blank=True)
    company_size = models.CharField(max_length=50, choices=COMPANY_SIZE_CHOICES)
    about_company = models.TextField()
    company_logo = models.ImageField(upload_to='company_logos/', blank=True, null=True, validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'svg'], message='Only jpg, jpeg, png and svg image formats are allowed!')])
    registration_document = models.FileField(upload_to='registration_docs/', blank=True, null=True, validators=[FileExtensionValidator(allowed_extensions=['docx', 'pdf', 'doc', ], message='Only pdf, docx, and doc document formats are allowed!')])
    job_posting_preference = models.CharField(max_length=8, choices=[('open', 'Open to All'), ('verified', 'Verified Only')])

    def clean(self):
        
        if self.company_logo:
            if self.company_logo.size > 3 * 1024 * 1024:
                raise ValidationError('Image file size exceeds the maximum size available for use')
            
            width, height = get_image_dimensions(self.company_logo)
            if width < 800 or height < 600:
                raise ValidationError('Image file size must be at least 800x600 pixels. ')
            
    def __str__(self):
        return f'{self.company_name} - {self.user.email}'


class SeekerProfile(Profile):
    full_name = models.CharField(max_length=255)
    job_type = models.CharField(max_length=6, choices=[('remote', 'Remote'), ('onsite', 'Onsite'), ('hybrid', 'Hybrid')])
    linkedin = models.URLField(blank=True)
    portfolio = models.URLField(blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    bio = models.TextField()
    skills = models.CharField(blank=True, help_text='Add skills related to your profession. You can add multiple skills.')
    experience = models.TextField()
    education = models.TextField()
    certifications = models.TextField(blank=True, null=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True, validators=[FileExtensionValidator(allowed_extensions=['docx', 'pdf', 'doc', ], message='Only pdf, docx, and doc document formats are allowed!')])
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True, validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'svg'], message='Only jpg, jpeg, png and svg image formats are allowed!')],)

    def clean(self):
        if self.profile_picture:
            if self.profile_picture.size > 3 * 1024 * 1024:
                raise ValidationError('Image file size exceeds the maximum size available for use')
            width, height = get_image_dimensions(self.profile_picture)
            if width < 800 or height < 600:
                raise ValidationError('Image file size must be at least 800x600 pixels. ')

    def __str__(self):
        return f'{self.full_name} - {self.user.email}'









class KnownDevice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='known_devices')
    user_agent = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.user_agent[:30]}"


class SecurityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    def __str__(self):
        return f'{self.user} --> {self.event}'
    

