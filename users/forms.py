import re
from .models import EmployerProfile, SeekerProfile
from django import forms
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import Country, State, COMPANY_SIZE_CHOICES
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

class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Email'}))


class ResetPasswordForm(forms.Form):
    current_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Enter your current password'}))
    new_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Enter your new password'}))
    confirm_new_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirm your new password'}))


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
    country = forms.ModelChoiceField(queryset=Country.objects.all().order_by('name'), empty_label="Select Country")
    state = forms.ModelChoiceField(queryset=State.objects.none(), empty_label="Select State")
    description = forms.CharField(widget=forms.Textarea)
    contact_number_code = forms.CharField(required=False, widget=forms.HiddenInput())


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        country_id = None

        # On POST, use submitted data
        if 'country' in self.data:
            try:
                country_id = int(self.data.get('country'))
            except (ValueError, TypeError):
                pass
        # On GET or initial, use initial data
        elif self.initial.get('country'):
            country_id = self.initial.get('country').id if hasattr(self.initial.get('country'), 'id') else self.initial.get('country')

        if country_id:
            self.fields['state'].queryset = State.objects.filter(country_id=country_id).order_by('name')
        else:
            self.fields['state'].queryset = State.objects.none()

    @classmethod
    def get_instance(cls, user):
        return {
            'company_name': user.employererprofile.company_name,
            'contact_number': user.employerprofile.contact_number,
            'country': user.employerprofile.country,
            'state': user.employerprofile.state,
            'description': user.employerprofile.description
        }


class SeekerBasicInfoForm(forms.Form):
    full_name = forms.CharField(max_length=100)
    phone_number = forms.CharField(max_length=15)
    country = forms.ModelChoiceField(queryset=Country.objects.all().order_by('name'), empty_label="Select Country")
    state = forms.ModelChoiceField(queryset=State.objects.none(), empty_label="Select State")
    bio = forms.CharField(widget=forms.Textarea)
    phone_number_code = forms.CharField(required=False, widget=forms.HiddenInput())


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        country_id = None

        # On POST, use submitted data
        if 'country' in self.data:
            try:
                country_id = int(self.data.get('country'))
            except (ValueError, TypeError):
                pass
        # On GET or initial, use initial data
        elif self.initial.get('country'):
            country_id = self.initial.get('country').id if hasattr(self.initial.get('country'), 'id') else self.initial.get('country')

        if country_id:
            self.fields['state'].queryset = State.objects.filter(country_id=country_id).order_by('name')
        else:
            self.fields['state'].queryset = State.objects.none()

    @classmethod
    def get_instance(cls, user):
        return {
            'full_name': user.seekerprofile.full_name,
            'phone_number': user.seekerprofile.phone_number,
            'country': user.seekerprofile.country,
            'state': user.seekerprofile.state,
            'bio': user.seekerprofile.bio
        }



class EmployerAccountForm(forms.ModelForm):
    company_website = forms.URLField(
        widget=forms.URLInput(attrs={'placeholder': 'https://yourcompany.com', 'class': 'form-control modern-url'})
    )
    company_logo = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control file-input', 'accept': 'image/*'})
    )
    registration_document = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control file-input', 'accept': '.pdf,.doc,.docx'})
    )
    company_size = forms.ChoiceField(
        choices=COMPANY_SIZE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = EmployerProfile
        fields = [
            'company_website', 'industry', 'company_size',
            'about_company', 'company_logo', 'registration_document', 'job_posting_preference'
        ]
        widgets = {
            'about_company': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }

class SeekerAccountForm(forms.ModelForm):
    skills = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Add skills (comma separated)', 'id': 'id_skills'})
    )
    resume = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control file-input', 'accept': '.pdf,.doc,.docx'})
    )
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control file-input', 'accept': 'image/*'})
    )

    class Meta:
        model = SeekerProfile
        fields = [
            'skills', 'experience', 'education', 'certifications',
            'resume', 'profile_picture', 'job_type', 'linkedin', 'portfolio'
        ]
        widgets = {
            'experience': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'education': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'certifications': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'linkedin': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/in/yourprofile'}),
            'portfolio': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://yourportfolio.com'}),
        }


class LoginForm(forms.Form):
    # email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Email'}))
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))



from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

class UpdateEmailForm(forms.Form):
    new_email = forms.EmailField(
        label="New Email Address",
        widget=forms.EmailInput(attrs={
            'placeholder': 'new@example.com',
            'autocomplete': 'email',
            'class': 'form-input'
        })
    )
    
    password = forms.CharField(
        label="Current Password",
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'autocomplete': 'current-password',
            'class': 'form-input'
        }),
        strip=False
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

    def clean_new_email(self):
        new_email = self.cleaned_data.get('new_email')
        if new_email.lower() == self.user.email.lower():
            raise ValidationError("New email cannot be the same as current email")
        return new_email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.user.check_password(password):
            raise ValidationError("Incorrect password")
        return password