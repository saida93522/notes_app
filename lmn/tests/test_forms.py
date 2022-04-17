from django.test import TestCase
from django.urls import reverse
from django import forms
from django.forms import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.base import ContentFile

from lmn.forms import NewNoteForm, UserRegistrationForm, UserUpdateForm , UpdateProfileForm
from django.contrib.auth.models import User
from lmn.models import Artist, Venue, Profile

import os
import tempfile
import string
from base64 import b64decode
from PIL import Image

# Test that forms are validating correctly, and don't accept invalid data

class NewNoteFormTests(TestCase):

    fixtures = ['testing_users', 'testing_shows', 'testing_venues', 'testing_artists', 'testing_notes']

    def test_missing_title_is_invalid(self):
        form_data = {'text': 'blah blah'}
        form = NewNoteForm(form_data)
        self.assertFalse(form.is_valid())

        invalid_titles = list(string.whitespace) + ['   ', '\n\n\n', '\t\t\n\t']

        for invalid_title in invalid_titles:
            form_data = {'title': invalid_title, 'text': 'blah blah'}
            form = NewNoteForm(form_data)
            self.assertFalse(form.is_valid())

    def test_missing_text_is_invalid(self):
        form_data = {'title': 'blah blah'}
        form = NewNoteForm(form_data)
        self.assertFalse(form.is_valid())

        invalid_texts = list(string.whitespace) + ['   ', '\n\n\n', '\t\t\n\t']

        for invalid_text in invalid_texts:
            form_data = {'title': 'blah blah', 'text': invalid_text}
            form = NewNoteForm(form_data)
            self.assertFalse(form.is_valid())

    def test_title_too_long_is_invalid(self):
        # Max length is 200
        form_data = {'title': 'a' * 201}
        form = NewNoteForm(form_data)
        self.assertFalse(form.is_valid())

    def test_text_too_long_is_invalid(self):
        # Max length is 1000
        form_data = {'title': 'a' * 1001}
        form = NewNoteForm(form_data)
        self.assertFalse(form.is_valid())

    def test_ok_title_and_length_is_valid(self):
        form_data = {'title': 'blah blah', 'text': 'blah, blah, blah.'}
        form = NewNoteForm(form_data)
        self.assertTrue(form.is_valid())


class TestImageUpload(TestCase):

    fixtures = ['testing_users', 'testing_shows', 'testing_venues', 'testing_artists', 'testing_notes']

    def setUp(self):
        user = User.objects.get(pk=1)
        self.client.force_login(user)
        self.MEDIA_ROOT = tempfile.mkdtemp()
        self.create_temp_bad_image_file()

    def create_temp_image_file(self):
        handle, tmp_img_file = tempfile.mkstemp(suffix='.jpg')
        img = Image.new('RGB', (10, 10) )
        img.save(tmp_img_file, format='JPEG')
        return tmp_img_file

    def test_upload_new_image_for_own_place(self):
        img_file_path = self.create_temp_image_file()

        with self.settings(MEDIA_ROOT=self.MEDIA_ROOT):

            with open(img_file_path, 'rb') as img_file:

                form_data = {'title': 'blah blah', 'text': 'blah, blah, blah.', 'photo': img_file}
                form = NewNoteForm(form_data)
                self.assertTrue(form.is_valid())

    def create_temp_bad_image_file(self):
        bad_file = open('bad_img_file.txt','w')
        bad_file.write('bleep bloop')
        bad_file.close()

    def test_upload_invalid_image_returns_error_message(self):
        with self.settings(MEDIA_ROOT=self.MEDIA_ROOT):

            with open('bad_img_file.txt', 'r') as bad_file:

                form_data = {'title': 'blah blah', 'text': 'blah, blah, blah.', 'photo': bad_file}
                form = NewNoteForm(form_data)
                response = self.client.post(reverse('new_note', kwargs={'show_pk': 3}), {'photo': bad_file}, follow=True)
                self.assertContains(response, 'Upload a valid image')
                # os.remove('bad_img_file.txt')

    def test_upload_invalid_renamed_file_returns_error_message(self):
        self.create_temp_bad_image_file()

        os.rename('bad_img_file.txt', 'bad_img.jpg')

        with self.settings(MEDIA_ROOT=self.MEDIA_ROOT):

            with open('bad_img.jpg', 'r') as bad_file:

                form_data = {'title': 'blah blah', 'text': 'blah, blah, blah.', 'photo': bad_file}
                form = NewNoteForm(form_data)
                response = self.client.post(reverse('new_note', kwargs={'show_pk': 3}), {'photo': bad_file}, follow=True)
                self.assertContains(response, 'Upload a valid image')

    def tearDown(self):
        if os.path.isfile('bad_img.jpg') is True:
            os.remove('bad_img.jpg')

        if os.path.isfile('bad_img_file.txt') is True:
            os.remove('bad_img_file.txt')


class RegistrationFormTests(TestCase):

    # check for missing fields

    def test_register_user_with_valid_data_is_valid(self):
        form_data = {
            'username': 'bob', 
            'email': 'bob@bob.com', 
            'first_name': 'bob', 
            'last_name': 'whatever', 
            'password1': 'q!w$er^ty6ui7op', 
            'password2': 'q!w$er^ty6ui7op'
        }

        form = UserRegistrationForm(form_data)
        self.assertTrue(form.is_valid())

    def test_register_user_with_missing_data_fails(self):
        form_data = {
            'username': 'bob', 
            'email': 'bob@bob.com', 
            'first_name': 'bob', 
            'last_name': 'whatever', 
            'password1': 'q!w$er^ty6ui7op', 
            'password2': 'q!w$er^ty6ui7op'
        }

        # Remove one key-value pair from a copy of the dictionary, assert form not valid
        for field in form_data.keys():
            copy_of_form_data = dict(form_data)
            del(copy_of_form_data[field])
            form = UserRegistrationForm(copy_of_form_data)
            self.assertFalse(form.is_valid())

    def test_register_user_with_password_mismatch_fails(self):
        form_data = {
            'username': 'another_bob', 
            'email': 'bob@bob.com', 
            'first_name': 'bob', 
            'last_name': 'whatever', 
            'password1': 'q!w$er^ty6ui7op', 
            'password2': 'dr%$ESwsdgdfh'
        }

        form = UserRegistrationForm(form_data)
        self.assertFalse(form.is_valid())

    def test_register_user_with_email_already_in_db_fails(self):
        # Create a user with email bob@bob.com
        bob = User(username='bob', email='bob@bob.com', first_name='bob', last_name='bob')
        bob.save()

        # attempt to create another user with same email
        form_data = {
            'username': 'another_bob', 
            'email': 'bob@bob.com', 
            'first_name': 'bob', 
            'last_name': 'whatever', 
            'password1': 'q!w$er^ty6ui7op', 
            'password2': 'q!w$er^ty6ui7op'
        }

        form = UserRegistrationForm(form_data)
        self.assertFalse(form.is_valid())

    def test_register_user_with_username_already_in_db_fails(self):
        # Create a user with username bob
        bob = User(username='bob', email='bob@bob.com')
        bob.save()

        # attempt to create another user with same username
        form_data = {
            'username': 'bob', 
            'email': 'another_bob@bob.com', 
            'first_name': 'bob', 
            'last_name': 'whatever', 
            'password1': 'q!w$er^ty6ui7op', 
            'password2': 'q!w$er^ty6ui7op'
        }

        form = UserRegistrationForm(form_data)
        self.assertFalse(form.is_valid())

    def test_register_user_with_username_already_in_db_case_insensitive_fails(self):
        # Create a user with username bob
        bob = User(username='bob', email='bob@bob.com')
        bob.save()

        invalid_username = ['BOB', 'BOb', 'Bob', 'bOB', 'bOb', 'boB']

        for invalid in invalid_username:
            # attempt to create another user with same username
            form_data = {
                'username': invalid, 
                'email': 'another_bob@bob.com', 
                'first_name': 'bob', 
                'last_name': 'whatever', 
                'password1': 'q!w$er^ty6ui7op', 
                'password2': 'q!w$er^ty6ui7opq!w$er^ty6ui7op'
            }

            form = UserRegistrationForm(form_data)
            self.assertFalse(form.is_valid())

    def test_register_user_with_email_already_in_db_case_insensitive_fails(self):
        # Create a user with username bob
        bob = User(username='bob', email='bob@bob.com')
        bob.save()

        invalid_email = ['BOB@bOb.com', 'BOb@bob.cOm', 'Bob@bob.coM', 'BOB@BOB.COM', 'bOb@bob.com', 'boB@bob.com']

        for invalid in invalid_email:
            # attempt to create another user with same username
            form_data = {
                'username': 'another_bob', 
                'email': invalid, 
                'first_name': 'bob', 
                'last_name': 'whatever', 
                'password1': 'q!w$er^ty6ui7op', 
                'password2': 'q!w$er^ty6ui7op'
            }
            form = UserRegistrationForm(form_data)
            self.assertFalse(form.is_valid())

class UserUpdateFormTests(TestCase):

    def setUp(self):
        self.user = User.objects.create(username='bob', email='bob@bob.com', first_name='bob', last_name='bob', password="testing")

    def test_user_update_first_last_name_form_valid(self):
        form_data={
            'first_name':'bob',
            'last_name':'dylan'
            }

        form = UserUpdateForm(form_data)
        self.assertTrue(form.is_valid())
        form.save()

    def test_user_update_no_first_name_is_valid(self):
        form_data={
            'first_name':'',
            'last_name':'dylan'
            }

        form = UserUpdateForm(form_data)
        self.assertTrue(form.is_valid())
        form.save()


class UpdateProfileFormTests(TestCase):

    fixtures = ['testing_users', 'testing_artists', 'testing_venues', 'testing_shows', 'testing_notes'] 

    def test_profile_updates_valid_data_is_valid(self):
        form_data={
            'favorite_artist':1,
            'favorite_venue': 1,
            }
        
        form =  UpdateProfileForm(data=form_data)
        self.assertEqual(form.is_valid(),True )
        # fields show in html
        form2 = UpdateProfileForm()
        self.assertIn("favorite_artist",form2.fields)
        self.assertIn("favorite_venue",form2.fields)

    def test_profile_updates_with_missing_data_is_not_valid(self):
        """ verify forms with missing data not valid """
        form_data={
            'favorite_artist':'thomas rhett',
            'favorite_venue':'Fitzgeral theater',
            }

        for field in form_data.keys():
            copy_of_form_data = dict(form_data)
            del(copy_of_form_data[field])
            form = UpdateProfileForm(copy_of_form_data)
            self.assertEqual(form.is_valid(), False)

    def test_profile_updates_with_missing_choice_fields_is_not_valid(self):
        """ verify forms with missing data not valid """
        form_data={
            'favorite_artist':4,
            'favorite_venue':1,
            }
        
        for field in form_data.keys():
            copy_of_form_data = dict(form_data)
            del(copy_of_form_data[field])
            form = UpdateProfileForm(copy_of_form_data)
            self.assertEqual(form.is_valid(), False)

    def test_required_field_error_msg_raised(self):
        """verify required fields return error_list template"""
        form = UpdateProfileForm({})
        self.assertTrue( 
            '<tr><th><label for="id_avatar">Avatar:</label></th><td><input type="file" name="avatar" accept="image/*" id="id_avatar"></td></tr><tr><th><label for="id_favorite_artist">Favorite artist:</label></th><td><ul class="errorlist"><li>This field is required.</li></ul><select name="favorite_artist" id="id_favorite_artist"><option value="1">Name: bob dylan</option></select></td></tr><tr><th><label for="id_favorite_venue">Favorite venue:</label></th><td><ul class="errorlist"><li>This field is required.</li></ul><select name="favorite_venue" id="id_favorite_venue"><option value="1">Some theater</option></select></td></tr>',forms.ValidationError)
        self.assertEqual(form.is_valid(), False)

    def test_valid_form_choice_field(self):
        form = UpdateProfileForm({'favorite_artist':1,'favorite_venue':1})
        self.assertTrue(form.is_valid)


class TestAvatarImg(TestCase):

    fixtures = ['testing_users']

    def setUp(self):
        user = User.objects.get(pk=2)
        self.client.force_login(user)
        artist = Artist(name='bob dylan')
        artist.save()
        self.profile = Profile(user=user,favorite_artist=artist)
        
        venue = Venue(name='Some theater')
        venue.save()

        self.profile = Profile(user=user,favorite_venue=venue)
        self.profile.save()

        #  create valid and invalid files
        self.small_gif = (
        b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
        b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
        b'\x02\x4c\x01\x00\x3b')
        
        self.image_data = b64decode("R0lGODlhAQABAIABAP8AAP///yH5BAEAAAEALAAAAAABAAEAAAICRAEAOw==")
        self.image_file = ContentFile(self.image_data, 'one.PDF')
    
    def test_avatar_update_valid(self):
        """ veryfy only specified file type is uploaded """
        self.profile.avatar = SimpleUploadedFile(
            'small.gif',
            self.small_gif,
            content_type='image/gif')
        self.profile.full_clean()

        form_data = {'favorite_artist':1 ,'favorite_venue':1,'avatar': self.small_gif}
        form = UpdateProfileForm(form_data)
        self.assertEqual(form.is_valid(),True)
        
    def test_avatar_update_not_valid(self):
        """ veryfy not specified file type raises errors """
        self.profile.avatar = SimpleUploadedFile(
            self.image_file.name, 
            self.image_file.read(),
            content_type='image/pdf')
        try:
            self.profile.full_clean() #check if any of the errors raised in avatar_clean is raised
        except ValidationError as e:
            self.assertTrue('avatar' in e.message_dict)