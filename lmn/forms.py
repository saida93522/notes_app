from django import forms

from .models import Note, Profile, Artist, Venue

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import ValidationError
from django.core.files.uploadedfile import UploadedFile


class VenueSearchForm(forms.Form):
    search_name = forms.CharField(label='Venue Name', max_length=200)


class ArtistSearchForm(forms.Form):
    search_name = forms.CharField(label='Artist Name', max_length=200)


class NewNoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ('title', 'text', 'photo')


class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def clean_username(self):
        username = self.cleaned_data['username']

        if not username:
            raise ValidationError('Please enter a username')

        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError('A user with that username already exists')

        return username

    def clean_first_name(self):
        first_name = self.cleaned_data['first_name']

        if not first_name:
            raise ValidationError('Please enter your first name')

        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data['last_name']

        if not last_name:
            raise ValidationError('Please enter your last name')

        return last_name

    def clean_email(self):
        email = self.cleaned_data['email']

        if not email:
            raise ValidationError('Please enter an email address')

        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('A user with that email address already exists')

        return email

    def save(self, commit=True):
        user = super(UserRegistrationForm, self).save(commit=False)
        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()

        return user


class UserUpdateForm(forms.ModelForm):
    """User models fields to update. """
    class Meta:
        model = User
        fields = ('first_name', 'last_name')


class ModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, field):
        return f"{field.name}"


class UpdateProfileForm(forms.ModelForm):
    """Profile model fields to update. """
    favorite_artist = ModelChoiceField(queryset=Artist.objects.all(), initial=0)
    favorite_venue= ModelChoiceField(queryset=Venue.objects.all(), initial=0)
    
    class Meta:
        model = Profile
        fields = ('avatar','favorite_artist','favorite_venue')

    def clean_avatar(self):
        """Validate user uploads only an image content type

        Raises:
            forms.ValidationError: raise error if user uploads content that is not an image
        Returns:
            [avatar]: current avatar
        """
        avatar = self.cleaned_data['avatar']
        try:
            if avatar and isinstance(avatar, UploadedFile): 
                # verify image content type when avatar is an imageField object and when it is an instance.
                img_name, sub = avatar.content_type.split('/')  #sub=.type
                if not(img_name == 'image' and sub in ['pjpeg','jpeg','png']):
                    print('Wrong type of image content.')
                    raise forms.ValidationError('Unsupported image type. Please upload only PNG and JPEG images.')
        except AttributeError as e:
            print(e)
        return avatar

    def save(self,commit=True):
        profile_user = super(UpdateProfileForm, self).save(commit=False)
        profile_user.avatar = self.cleaned_data['avatar']

        if commit:
            profile_user.save() 

        return profile_user