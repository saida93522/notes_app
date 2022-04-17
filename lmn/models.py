from django.db import models
from django.core.files.storage import default_storage
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils import timezone

from django.contrib.auth.models import User
User._meta.get_field('email')._unique = True

#  Require email, first name and last name
User._meta.get_field('email')._blank = False
User._meta.get_field('last_name')._blank = False
User._meta.get_field('first_name')._blank = False

class Profile(models.Model):
    """ Represents the db model for an existing user."""
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, primary_key=True)
    favorite_artist = models.ForeignKey('Artist', on_delete=models.CASCADE, null=True, blank=True)
    favorite_venue = models.ForeignKey('Venue', on_delete=models.CASCADE, null=True, blank=True)
    avatar = models.ImageField(default='default.jpg',upload_to='profile_images', null=True, blank=True)
    objects = models.Manager()


    @receiver(post_save, sender=User)
    def create_save_user_profile(sender, created, instance, **kwargs):
        """create and save profile automatically when a user is created.
        Args:
            sender ([User]): User notifies this function that a new user being created in db
            created ([Profile]): create and save a profile instance for this user
        """
        #if new user created, create new profile
        if created:
            Profile.objects.create(user=instance)

    def save(self, *args, **kwargs):
        """ delete/update avatar, then save updates. """
        profile = Profile.objects.filter(pk=self.pk).first()
        if profile and profile.avatar:
            if profile.avatar != self.avatar:
                self.delete_photo(profile.avatar)
                if not self.avatar:
                    self.avatar = 'default.jpg'
        super().save(*args, **kwargs)
        
    def delete_photo(self, avatar):
        """remove photo from profile object. """
        if default_storage.exists(avatar.name):
            default_storage.delete(avatar.name)

    def delete(self,  *args, **kwargs):
        """remove photo from profile object and from media file."""
        if self.avatar:
            self.delete_photo(self.avatar)
            
        super().delete(*args, **kwargs)

    def __str__(self):
        """ Return string representation of our user. """
        favorite_artist_str = self.favorite_artist if self.favorite_artist else 'No favorite artist.'
        favorite_venue_str = self.favorite_venue if self.favorite_venue else 'No favorite venue.'
        avatar_str = self.avatar.url if self.avatar else 'No avatar.'
        return str(f'Name: {self.user.first_name} {self.user.last_name}, Favorite Artist: {favorite_artist_str}, Favorite Venue: {favorite_venue_str}\nAvatar: {avatar_str}')


class Artist(models.Model):
    """ Represents a musician or a band - a music artist. """
    name = models.CharField(max_length=200, blank=False, unique=True)
    objects = models.Manager()
    
    def __str__(self):
        return f'Name: {self.name}'


class Venue(models.Model):
    """ Represents a venue, that hosts shows. """
    name = models.CharField(max_length=200, blank=False, unique=True)
    city = models.CharField(max_length=200, blank=False)
    state = models.CharField(max_length=200, blank=False)
    objects = models.Manager()
    
    def __str__(self):
        return f'Name: {self.name} Location: {self.city}, {self.state}'


class Show(models.Model):
    """ One Artist playing at one Venue at a particular date and time. """
    show_date = models.DateTimeField(blank=False)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE)
    objects = models.Manager()

    class Meta:
        constraints = [models.UniqueConstraint(fields=['show_date', 'artist', 'venue'], name='instance_of_a_show')]

    @property
    def in_past(self):
        return self.show_date < timezone.now()

    def __str__(self):
        return f'Artist: {self.artist} At: {self.venue} On: {self.show_date}'


class Note(models.Model):
    """ One user's opinion of one Show. """
    show = models.ForeignKey(Show, blank=False, on_delete=models.CASCADE)
    user = models.ForeignKey('auth.User', blank=False, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, blank=False)
    text = models.TextField(max_length=1000, blank=False)
    posted_date = models.DateTimeField(auto_now_add=True, blank=False)
    photo = models.ImageField(upload_to='user_images/', blank=True, null=True)
    objects = models.Manager()

    class Meta:
        constraints = [models.UniqueConstraint(fields=['show', 'user'], name='one_user_note_per_show')]

    def save(self, *args, **kwargs):

        if timezone.now() < self.show.show_date:
            raise ValidationError('Can\'t add note for show that hasn\'t happened yet.')

        # delete old photo if note and old photo exist, and new photo present
        old_note = Note.objects.filter(pk=self.pk).first()
        if old_note and old_note.photo:
            if old_note.photo != self.photo:
                self.delete_photo(old_note.photo)
        super().save(*args, **kwargs) 

    def delete_photo(self, photo):
        if default_storage.exists(photo.name):
            default_storage.delete(photo.name)

    def delete(self, *args, **kwargs):
        if self.photo:
            self.delete_photo(self.photo)
        super().delete(*args, **kwargs)

    def __str__(self):
        photo_str = self.photo.url if self.photo else 'No photo.'
        return f'User: {self.user} Show: {self.show} Note title: {self.title} \
        Text: {self.text} Posted on: {self.posted_date} \
        Photo: {photo_str}'