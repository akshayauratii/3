from django import forms
from django.contrib.auth.models import User
from .models import Profile, TeaTimeSession, CommunityPost, Opportunity

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    user_type = forms.ChoiceField(choices=Profile.USER_TYPE_CHOICES)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        user_type = cleaned_data.get("user_type")
        username = cleaned_data.get("username")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
            
        if user_type == 'admin':
            allowed_admins = ['Akshaya', 'Ramya', 'Harini', 'Divya', 'Akanksha']
            allowed_email = 'almamate@gmail.com'
            
            # Name check
            if username and username.lower() not in [name.lower() for name in allowed_admins]:
                raise forms.ValidationError(f"Admin registration is restricted. Authorized names: {', '.join(allowed_admins)}")
            
            # Email check
            email = cleaned_data.get('email')
            if email and email.lower() != allowed_email.lower():
                raise forms.ValidationError(f"Admin registration requires the official email: {allowed_email}")
                
        return cleaned_data

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Your Name'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Your Email'}))
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 5, 'placeholder': 'How can we help?'}))

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'profile_picture', 'skills', 'government_internships', 'private_internships_jobs']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Tell us about yourself...'}),
            'skills': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Comma-separated (e.g. Python, Leadership)'}),
            'government_internships': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Details of any government internships...'}),
            'private_internships_jobs': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Details of private internships or jobs...'}),
        }

class TeaTimeSessionForm(forms.ModelForm):
    class Meta:
        model = TeaTimeSession
        fields = ['topic', 'description', 'date_time', 'meeting_link']
        widgets = {
            'topic': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Session Topic'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Brief description'}),
            'date_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'meeting_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://meet.google.com/...'}),
        }

class CommunityPostForm(forms.ModelForm):
    class Meta:
        model = CommunityPost
        fields = ['content', 'image', 'category']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Share your achievement, certificate, or project...'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }

class OpportunityForm(forms.ModelForm):
    class Meta:
        model = Opportunity
        fields = ['title', 'description', 'type', 'category', 'stipend_type', 'domain', 'company', 'location', 'min_assessment_score']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Software Engineer Intern'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Job responsibilities, requirements...'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'stipend_type': forms.Select(attrs={'class': 'form-control'}),
            'domain': forms.Select(attrs={'class': 'form-control'}),
            'company': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company Name'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Remote, Bangalore'}),
            'min_assessment_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 30}),
        }

