from taggit.forms import TagWidget
from django import forms
from .models import JobApplication, JobPosting

class PostJobForm(forms.ModelForm):
    class Meta:
        model = JobPosting
        fields = [
            'title', 'job_type', 'location', 'salary', 
            'experience_required', 'qualifications', 'deadline',
            'job_category', 'job_status', 'skills_required'
        ]
        widgets = {
            'skills_required': forms.TextInput(attrs={
                'class': 'tagify-input',
                'placeholder': 'Type skills and press Enter'
            }),
            'deadline': forms.DateInput(attrs={'type': 'date'}),
        }



class ApplyForJobForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = [
            'cover_letter','resume','attachments',
        ]
    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data
    


class PublicContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea, max_length=2000)



