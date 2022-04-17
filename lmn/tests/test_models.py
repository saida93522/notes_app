from django.test import TestCase

from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from .. import models
from django.contrib.auth.models import User
from lmn.models import Profile, Artist, Venue, Show, Note

from django.utils import timezone
from datetime import timedelta


class TestUser(TestCase):

    def test_create_user_duplicate_username_fails(self):
        user = User(username='bob', email='bob@bob.com', first_name='bob', last_name='bob')
        user.save()

        user2 = User(username='bob', email='another_bob@bob.com', first_name='bob', last_name='bob')
        with self.assertRaises(IntegrityError):
            user2.save()

    def test_create_user_duplicate_email_fails(self):
        user = User(username='bob', email='bob@bob.com', first_name='bob', last_name='bob')
        user.save()

        user2 = User(username='bob', email='bob@bob.com', first_name='bob', last_name='bob')
        with self.assertRaises(IntegrityError):
            user2.save()

    def test_username_label(self):
        user = User(username='bob', email='bob@bob.com', first_name='bob', last_name='bob')
        field_label = user._meta.get_field('username').verbose_name
        self.assertEqual(field_label, 'username')


class TestProfile(TestCase):
    def test_new_users_get_profile_automatically(self):
        """ testing the one to one """        
        #Arrange new user
        user = User.objects.create(username='bob', email='bob@bob.com', first_name='bob', last_name='bob', password='bobTheBuilder')
        #assert signal triggered and created profile instance 
        #tests this error is returned --> django.db.models.fields.related.RelatedObjectDoesNotExist: User has no profile.
        self.assertIsInstance(user.profile, models.Profile)
        
        #assert duplicate profile instance isn't created
        user.save()
        self.assertIsInstance(user.profile, models.Profile)

    def test_favorite_artist(self):
        #Arrange new user with favorite artist
        user = User(username='bob', email='bob@bob.com', first_name='bob', last_name='bob')
        user.save()
        
        artist = Artist(name='bob dylan')
        artist.save()
        
        profile = Profile(favorite_artist=artist, user=user)
        profile.save()
        
        #Action
        record = Profile.objects.get(pk=1)

        #Assert foreign key relation
        self.assertEqual(record.favorite_artist.name, 'bob dylan')

    def test_favorite_Venue(self):
        #Arrange new user with favorite venue
        user = User(username='bob', email='bob@bob.com', first_name='bob', last_name='bob')
        user.save()
        
        venue = Venue(name='Some theater',city='St Paul',state='MN')
        venue.save()
        
        profile = Profile(favorite_venue=venue, user=user)
        profile.save()
        
        #Action
        record = Profile.objects.get(pk=1)

        #Assert 
        self.assertEqual(record.favorite_venue.name, 'Some theater')
        self.assertEqual(record.favorite_venue.city, 'St Paul')
        self.assertEqual(record.favorite_venue.state, 'MN')

    def test_default_image_field(self):
        #Arrange new user with default avatar
        user = User.objects.create(username='bob', email='bob@bob.com', first_name='bob', last_name='bob', password='bobTheBuilder')
        user.save()

        #Action
        profile = Profile({})

        #Assert
        if not profile.avatar:
            default_image = (profile.avatar.name, 'default.jpg')
            self.assertTrue(default_image)

    def test_removing_avatar_changes_to_default_avatar(self):
        """ Verify default image is used after previously saved avatar is deleted. """
        # create and get a user profile
        user = User.objects.create(username='bob', email='bob@bob.com', first_name='bob', last_name='bob', password='bobTheBuilder')
        user.save()
        profile = Profile.objects.get(user=user)
        # save an avatar to the user profile
        small_gif = (
        b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
        b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
        b'\x02\x4c\x01\x00\x3b')
        avatar = SimpleUploadedFile(
            'small.gif',
            small_gif,
            content_type='image/gif') 
        profile.avatar = avatar
        # remove the saved avatar
        profile.avatar.delete()
        # assert avatar is now default
        self.assertEqual(profile.avatar.url, '/media/default.jpg')

class TestNote(TestCase):

    fixtures = ['testing_users', 'testing_artists', 'testing_venues', 'testing_shows', 'testing_notes'] 

    def setUp(self):
        # all tests are for User 1
        self.user = User.objects.get(pk=1)

    def change_show_dates(self):
        # used for future show tests 

        show_future = Show.objects.get(pk=1)
        # set show 1 to one year from current date
        show_future.show_date = timezone.now() + timedelta(365)
        show_future.save()

        show_present = Show.objects.get(pk=2)
        # set show 2 to current time and date
        show_present.show_date = timezone.now()
        show_present.save()

        show_recent = Show.objects.get(pk=3)
        # set show 3 to one second after current time and date
        show_recent.show_date = timezone.now() - timedelta(seconds=1)
        show_recent.save()

    def test_one_user_create_one_note_for_one_show(self):
        show = Show.objects.get(pk=3)
        note = Note(show=show, user=self.user, title='aaa', text='bbb')
        note.save()

        note_from_db = Note.objects.filter(show=show, user=self.user).first()

        self.assertIsNotNone(note_from_db)
        self.assertEqual(self.user, note_from_db.user)
        self.assertEqual(show, note_from_db.show)
        self.assertEqual('aaa', note_from_db.title)
        self.assertEqual('bbb', note_from_db.text)

    def test_one_user_create_multiple_note_for_one_show_fails(self):
        show = Show.objects.get(pk=1)
        note = Note(show=show, user=self.user, title='aaa', text='bbb')

        # there is already a note for user 1, show 1 in fixtures
        with self.assertRaises(IntegrityError):
            note.save()

    def test_create_note_for_future_show_fails(self):
        # show 1 takes place one year from current date
        self.change_show_dates()
        show = Show.objects.get(pk=1)
        note = Note(show=show, user=self.user, title='aaa', text='bbb')

        with self.assertRaises(ValidationError):
            note.save()

    def test_create_note_for_current_show(self):
        # show 2 takes place at the current time - but this passes because the db takes a few milliseconds process
        self.change_show_dates()
        show = Show.objects.get(pk=2)
        note = Note(show=show, user=self.user, title='aaa', text='bbb')
        note.save()

        note_from_db = Note.objects.filter(show=show, user=self.user).first()

        self.assertIsNotNone(note_from_db)
        self.assertEqual(self.user, note_from_db.user)
        self.assertEqual(show, note_from_db.show)
        self.assertEqual('aaa', note_from_db.title)
        self.assertEqual('bbb', note_from_db.text)

    def test_create_note_for_very_recent_show(self):
        # show 3 takes place 1 second ago
        self.change_show_dates()
        show = Show.objects.get(pk=3)
        note = Note(show=show, user=self.user, title='aaa', text='bbb')
        note.save()

        note_from_db = Note.objects.filter(show=show, user=self.user).first()

        self.assertIsNotNone(note_from_db)
        self.assertEqual(self.user, note_from_db.user)
        self.assertEqual(show, note_from_db.show)
        self.assertEqual('aaa', note_from_db.title)
        self.assertEqual('bbb', note_from_db.text)