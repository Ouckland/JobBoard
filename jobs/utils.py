from users.models import EmployerProfile, SeekerProfile
from .models import Notification

def get_user_profile(user):
    try:
        return SeekerProfile.objects.get(user=user), 'seeker'
    except SeekerProfile.DoesNotExist:
        try:
            return EmployerProfile.objects.get(user=user), 'employer'
        except EmployerProfile.DoesNotExist:
            return None, None

# 
def create_notification(recipient, message, url=None):
    Notification.objects.create(
        recipient=recipient,
        message=message,
        url=url
    )
    

def calculate_profile_completion(profile, profile_type):
    seeker_fields = [
        'full_name', 'job_type', 'linkedin', 'portfolio', 'phone_number',
        'bio', 'skills', 'experience', 'education', 'certifications',
        'resume', 'profile_picture'
    ]

    employer_fields = [
        'company_name', 'company_website', 'industry', 'contact_number',
        'description', 'company_size', 'about_company',
        'company_logo', 'registration_document'
    ]

    fields = seeker_fields if profile_type == 'seeker' else employer_fields

    total = len(fields)
    filled = sum(bool(getattr(profile, field)) for field in fields)
    percentage = int((filled / total) * 100)
    return percentage
