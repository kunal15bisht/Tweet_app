from django import forms
from .models import Tweet, Profile
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, User


class TweetForm(forms.ModelForm):
    class Meta:
        model = Tweet
        fields = ['text', 'photo']

    def __init__(self, *args, **kwargs):
        super(TweetForm, self).__init__(*args, **kwargs)
        self.fields['text'].widget.attrs.update({
            'class': 'form-control form-control-lg',  # larger input size
            'placeholder': 'What’s happening?',
            'rows': 4,
            'style': 'font-size: 1.1rem; padding: 15px; border-radius: 12px;'
        })
        self.fields['photo'].widget.attrs.update({
            'class': 'form-control form-control-lg',
            'style': 'padding: 10px; border-radius: 12px;'
        })
        self.fields['photo'].required = False


class UserRegistrationsForm(UserCreationForm):
    # We add email specifically because UserCreationForm doesn't require it by default
    email = forms.EmailField(
        required=True, 
        widget=forms.EmailInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Enter your email'
        })
    )
    class Meta:
        model = User
        # Only list model fields here. Passwords are handled by the parent class automatically.
        fields = ("username", "email") 
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # LOOP to apply styles instead of repeating lines
        for field_name in ['username', 'password1', 'password2']:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({
                    'class': 'form-control',
                    'placeholder': f"Enter your {field_name.replace('1', '').replace('2', '')}"
                })
    # --- KEY ADDITION: Validate Email Uniqueness Here ---
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email



class UserLoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your email',
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your password',
    }))



class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email']
    
    # Add styling
    def __init__(self, *args, **kwargs):
        super(UserUpdateForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your username',
        })
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your Email',
        })

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'profile_pic']

    # Add styling
    def __init__(self, *args, **kwargs):
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)
        self.fields['bio'].widget.attrs.update({
            'class': 'form-control form-control-lg',  # larger input size
            'placeholder': 'Add your Bio',
            'rows': 4,
            'style': 'font-size: 1.1rem; padding: 15px; border-radius: 12px;'
        })
        self.fields['profile_pic'].widget.attrs.update({
            'class': 'form-control form-control-lg',
            'style': 'padding: 10px; border-radius: 12px;'
        })
        self.fields['profile_pic'].required = False