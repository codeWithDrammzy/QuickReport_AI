from django import forms
from .models import *
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your phone number'
        })
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your address',
            'rows': 3
        })
    )

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'address',
            'password1', 'password2'
        ]  # Removed username and role fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove username field since we're using email
        self.fields.pop('username', None)
        
        # Add styling to password fields
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Create a strong password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError("A user with this phone number already exists.")
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        # Use email as username and set role as citizen
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data['phone']
        user.address = self.cleaned_data['address']
        user.role = 'citizen'  # Default role for self-registration
        
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email'
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            # Authenticate using email instead of username
            try:
                user = User.objects.get(email=email)
                user = authenticate(username=user.username, password=password)
                if user is None:
                    raise forms.ValidationError("Invalid email or password.")
                cleaned_data['user'] = user
            except User.DoesNotExist:
                raise forms.ValidationError("Invalid email or password.")
        
        return cleaned_data


# ... rest of your existing forms (OfficerForm, DepartmentForm, etc.) remain the same
class OfficerForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = Officer
        fields = ['rank', 'badge_number', 'department', 'profile_picture']

    def save(self, commit=True):
        # Create a new User account automatically
        user = User.objects.create_user(
            username=self.cleaned_data['email'],
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            password=self.cleaned_data['password'],
        )
        user.role = 'officer'
        user.save()

        officer = super().save(commit=False)
        officer.user = user
        if commit:
            officer.save()
        return officer


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = '__all__'
        exclude = ['is_active']


class CrimeSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        label='',
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by report ID, department, location, status, or type',
            'class': 'bg-blue-800 text-sm px-4 py-2 rounded-full focus:outline-none focus:ring-2 focus:ring-yellow-400 placeholder-gray-300 text-gray-100 w-full pr-10'
        })
    )


class CrimeReportForm(forms.ModelForm):
    # Add explicit fields for live capture
    photo_file = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'hidden'}))
    video_file = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'hidden'}))
    audio_file = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'hidden'}))
    
    class Meta:
        model = CrimeReport
        fields = [
            'title', 'description', 'location',
            'incident_type', 'department', 'priority',
            'latitude', 'longitude',  # ADD THESE
            'evidence_image', 'evidence_video', 'evidence_audio'
        ]
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 4, 
                'placeholder': 'Describe the incident in detail...',
                'class': 'border border-gray-300 rounded-lg px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'title': forms.TextInput(attrs={
                'placeholder': 'Enter report title',
                'class': 'border border-gray-300 rounded-lg px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'location': forms.TextInput(attrs={
                'placeholder': 'Enter location or use GPS button below',
                'class': 'border border-gray-300 rounded-lg px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'id': 'locationInput'
            }),
            'incident_type': forms.Select(attrs={
                'class': 'border border-gray-300 rounded-lg px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'department': forms.Select(attrs={
                'class': 'border border-gray-300 rounded-lg px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'priority': forms.Select(attrs={
                'class': 'border border-gray-300 rounded-lg px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'latitude': forms.HiddenInput(attrs={
                'id': 'latitudeField'
            }),
            'longitude': forms.HiddenInput(attrs={
                'id': 'longitudeField'
            }),
            'evidence_image': forms.ClearableFileInput(attrs={
                'class': 'hidden',
                'id': 'evidenceImageInput'
            }),
            'evidence_video': forms.ClearableFileInput(attrs={
                'class': 'hidden', 
                'id': 'evidenceVideoInput'
            }),
            'evidence_audio': forms.ClearableFileInput(attrs={
                'class': 'hidden',
                'id': 'evidenceAudioInput'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set required fields
        self.fields['title'].required = True
        self.fields['description'].required = True
        self.fields['location'].required = True
        self.fields['incident_type'].required = True
        self.fields['department'].required = True
        self.fields['priority'].required = True
    class Meta:
        model = CrimeReport
        fields = [
            'title', 'description', 'location',
            'incident_type', 'department', 'priority',
            'latitude', 'longitude',
            'evidence_image', 'evidence_video', 'evidence_audio'
        ]
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 4, 
                'placeholder': 'Describe the incident in detail...',
                'class': 'border border-gray-300 rounded-lg px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'title': forms.TextInput(attrs={
                'placeholder': 'Enter report title',
                'class': 'border border-gray-300 rounded-lg px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'location': forms.TextInput(attrs={
                'placeholder': 'Enter location or use GPS button below',
                'class': 'border border-gray-300 rounded-lg px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'id': 'locationInput'
            }),
            'incident_type': forms.Select(attrs={
                'class': 'border border-gray-300 rounded-lg px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'department': forms.Select(attrs={
                'class': 'border border-gray-300 rounded-lg px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'priority': forms.Select(attrs={
                'class': 'border border-gray-300 rounded-lg px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'latitude': forms.HiddenInput(attrs={
                'id': 'latitudeField'
            }),
            'longitude': forms.HiddenInput(attrs={
                'id': 'longitudeField'
            }),
            'evidence_image': forms.ClearableFileInput(attrs={
                'class': 'hidden',
                'id': 'photoFileInput'
            }),
            'evidence_video': forms.ClearableFileInput(attrs={
                'class': 'hidden', 
                'id': 'videoFileInput'
            }),
            'evidence_audio': forms.ClearableFileInput(attrs={
                'class': 'hidden',
                'id': 'audioFileInput'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set required fields
        self.fields['title'].required = True
        self.fields['description'].required = True
        self.fields['location'].required = True
        self.fields['incident_type'].required = True
        self.fields['department'].required = True
        self.fields['priority'].required = True
        
        # Add help texts
        self.fields['location'].help_text = "Enter address or use the GPS button to get your current location"
        self.fields['priority'].help_text = "Select the urgency level of this incident"
        self.fields['incident_type'].help_text = "Choose the type of incident"
        self.fields['department'].help_text = "Select which department should handle this report"