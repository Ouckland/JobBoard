import re
from .models import EmployerProfile
from django import forms
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import OTP

User = get_user_model()


class EmailSignupForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'password'}))

    def clean_email(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already exists")
        return email
    
    def clean_password(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d@!$?&]{8,}$'
        if not re.match(pattern, password):
            raise ValidationError('Password must contain at least 8 characters, one uppercase letter, one lowercase letter, one digit and one special character')
        
        return password

class PassewordResetRequestForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Email'}))

class PasswordResetForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}))

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d@!$?&]{8,}$'
        
        if password and not re.match(pattern, password):
            self.add_error('password', 'Password must contain at least 8 characters, one uppercase letter, one lowercase letter, one digit and one special character')
        
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match. Try again')
        
        return cleaned_data
    
            
class OTPform(forms.Form):
    otp = forms.CharField(max_length=6, min_length=6)

    # Override the constructor to accept user_email
    def __init__(self, *args, **kwargs):
        self.user_email = kwargs.pop('user_email', None)  # Pop the user_email argument
        super().__init__(*args, **kwargs)  # Call the parent constructor

    def clean_otp(self):
        otp = self.cleaned_data.get('otp')
        try:
            otp_object = OTP.objects.get(user_email=self.user_email, otp=otp)
            print(f"OTP created_at: {otp_object.created_at}")
            print(f"Current time: {timezone.now()}")

            if otp_object.is_expired:
                raise forms.ValidationError('OTP has expired')
        except OTP.DoesNotExist:
            raise forms.ValidationError('Invalid OTP')
        return otp

class ChooseAccountTypeForm(forms.Form):
    ACCOUNT_TYPE_CHOICES = [
        ('employer', 'Employer'),
        ('seeker', 'Job Seeker'),
    ]
    username = forms.CharField(widget=forms.TextInput)
    account_type = forms.ChoiceField(choices=ACCOUNT_TYPE_CHOICES, widget=forms.RadioSelect)

    def __init__(self, user_email, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_email = user_email  # Store email for later use


class EmployerBasicInfoForm(forms.Form):
    company_name = forms.CharField(max_length=100)
    contact_number = forms.CharField(max_length=15)
    country = forms.CharField()
    state = forms.CharField()
    description = forms.CharField(widget=forms.Textarea)



class EmployerAccountForm(forms.ModelForm):
    class Meta:
        model = EmployerProfile
        fields = [
            'company_website', 'industry', 'company_size', 
            'about_company', 'company_logo', 'registration_document', 'job_posting_preference'
        ]
        
        widgets = {
            'about_company': forms.Textarea(attrs={'rows': 4}),
        }


class SeekerBasicInfoForm(forms.Form):
    full_name = forms.CharField(max_length=100)
    phone_number = forms.CharField(max_length=15)
    country = forms.CharField()
    state = forms.CharField()
    bio = forms.CharField(widget=forms.Textarea)


from .models import SeekerProfile

class SeekerAccountForm(forms.ModelForm):
    class Meta:
        model = SeekerProfile
        fields = [
            'skills', 'experience', 'education', 'certifications', 
            'resume', 'profile_picture', 'bio', 'job_type', 'linkedin','portfolio'
        ]


        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'skills': forms.Textarea(attrs={'rows': 4}),
            'experience': forms.Textarea(attrs={'rows': 4}),
            'education': forms.Textarea(attrs={'rows': 4}),
            'certifications': forms.Textarea(attrs={'rows': 4}),
        }

class LoginForm(forms.Form):
    # email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Email'}))
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))


